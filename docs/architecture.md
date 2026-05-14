# HermitBench Architecture

HermitBench evaluates an LLM's ability to drive [OpenHermit](https://github.com/openhermit/openhermit) — a personal-agent gateway with persistent memory, skills, channels, and schedules — by running a fleet of small, deterministic tasks against a real `hermit` install. The harness scores each run automatically and reports cost-vs-quality across models.

```
┌─ host machine ───────────────────────────────────────────────┐
│                                                              │
│  eval/run_batch.py  ── ThreadPoolExecutor(max_workers=N) ──┐ │
│      │                                                     │ │
│      └── one task = one container = one model session      │ │
│                                                            │ │
│  ┌─ docker container: hermitbench-ubuntu:v0.1 ─────────────┘ │
│  │  127.0.0.1:<random>  ─→  container:4000  (gateway HTTP)   │
│  │                                                           │
│  │   postgresql-16              (hermit / hermit / hermit)   │
│  │   hermit gateway run         (foreground, GATEWAY_PORT=4000) │
│  │   /tmp_workspace             (bind-mounted from host)     │
│  │                                                           │
│  └───────────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

## The container

Built from `docker/Dockerfile` and tagged `hermitbench-ubuntu:v0.1`. The image bakes in:

- Ubuntu 22.04 + Node 20 + Bun
- PostgreSQL 16 (from the PGDG apt repo — Jammy only ships 14)
- `openhermit@latest` from npm, which provides the `hermit` and `openhermit` binaries
- `docker/entrypoint.sh`, `docker/healthcheck.sh`, `docker/seed_helpers.sh` at `/usr/local/bin/`

Baked-in environment:

```
DATABASE_URL=postgres://hermit:hermit@127.0.0.1:5432/hermit
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=4000
OPENHERMIT_GATEWAY_URL=http://127.0.0.1:4000
OPENHERMIT_AGENT_ID=main
TMP_WORKSPACE=/tmp_workspace
```

The Postgres cluster is initialised by the apt postinst at build time, but the cluster is not started during build (rootless buildkit blocks systemd). Postgres role + database creation is deferred to first boot inside `entrypoint.sh`, guarded by the flag `/var/lib/postgresql-state/.bootstrapped`.

## Lifecycle of a single task run

`run_single_task` in `eval/run_batch.py` drives this flow per task. The OpenHermit-specific glue lives in `src/agents/openhermit/runner.py` and `src/utils/docker_utils.py`.

### 1. Parse the task file

`src/utils/task_parser.py:parse_task_md` reads YAML frontmatter (`id`, `timeout_seconds`) plus `##` sections (`Prompt`, `Workspace Path`, `Automated Checks`, `Env`, `Seed SQL`, `Seed Post`). The workspace path resolves relative to the repo root.

### 2. Materialise seed blocks

Before the container starts, the runner writes the task's `## Seed SQL` and `## Seed Post` sections into the host workspace directory as `seed.sql` and `seed_post.sh`. The workspace is bind-mounted into the container at `/tmp_workspace`, so the entrypoint can pick them up.

```python
# src/agents/openhermit/runner.py
ws = Path(spec.workspace_path)
(ws / "seed.sql").write_text(seed_sql + "\n", ...)
(ws / "seed_post.sh").write_text(seed_post + "\n", ...)
```

### 3. Start the container

```bash
docker run -d --name <task_id> \
  --entrypoint /usr/local/bin/entrypoint.sh \
  -p 127.0.0.1:0:4000 --init \
  -v <workspace_host>:/tmp_workspace \
  hermitbench-ubuntu:v0.1
```

`-p 127.0.0.1:0:4000` lets the kernel pick a random host port. The runner discovers the actual port with `docker port <task_id> 4000/tcp`.

### 4. Entrypoint boots the gateway

`docker/entrypoint.sh` runs (in order):

1. `service postgresql start`, then waits up to 60s for `pg_isready`.
2. **Bootstrap on first run** (guarded by `/var/lib/postgresql-state/.bootstrapped`):
   ```
   CREATE USER hermit WITH PASSWORD 'hermit' SUPERUSER;
   CREATE DATABASE hermit OWNER hermit;
   ```
3. Generate `GATEWAY_ADMIN_TOKEN`, `GATEWAY_JWT_SECRET`, and a base64 32-byte `OPENHERMIT_SECRETS_KEY` if not already set in env. Write the admin token to `/root/.openhermit/admin_token` so the host runner can read it via `docker exec`.
4. Persist those env vars to `/etc/profile.d/hermitbench.sh` and `/etc/environment` so later `docker exec` shells see them.
5. **Apply `/tmp_workspace/seed.sql`** if present — runs against an empty `hermit` DB *before* gateway boot, so it can only seed tables that exist at this stage. (The OpenHermit Drizzle migrations run at gateway startup; tables like `memories`, `instructions`, `agent_policies` don't exist yet, so seed those in `seed_post.sh`.)
6. `hermit gateway run &` — foreground process; reads `GATEWAY_HOST` / `GATEWAY_PORT` from env.
7. Wait for `/health` via `docker/healthcheck.sh`.
8. **Apply `/tmp_workspace/seed_post.sh`** if present — runs CLI seeds against the live gateway (agent create, secret set, skill register, memory inserts).

### 5. Configure the agent over HTTP

The runner pulls the admin token from `/root/.openhermit/admin_token` and configures agent `main` for OpenRouter:

```
hermit agents create main || true
hermit agents enable main
hermit config --agent main secrets set OPENROUTER_API_KEY $KEY
hermit config --agent main set model.provider openrouter
hermit config --agent main set model.model <model>
```

Note: `--agent` is a flag on the `config` subcommand itself, not a top-level `hermit` flag. The API key is passed via shell-quoted positional args inside `docker exec` so it never appears in `docker inspect` output.

### 6. Drive one chat turn over the gateway HTTP API

The runner is an HTTP client. It does **not** spawn `hermit chat` (which is a Bubble Tea TUI and is unsuitable for automation). The two calls per task are:

```
POST http://127.0.0.1:<host_port>/api/agents/main/sessions
     Authorization: Bearer <admin_token>
     { "sessionId": "cli:<uuid>",
       "source": { "kind": "cli", "interactive": false } }

POST http://127.0.0.1:<host_port>/api/agents/main/sessions/<sid>/messages?wait=true&timeout=<ms>
     Authorization: Bearer <admin_token>
     { "text": "<task prompt>" }
```

`?wait=true` makes the gateway block until the agent finishes (or until `timeout` ms elapse). On timeout, the gateway returns HTTP 504 with a `SyncResponse` body; the runner surfaces this as an error rather than raising.

The `SyncResponse` (`{ sessionId, messageId?, text, toolCalls, error? }`) is saved to `output/<...>/session.json`.

### 7. Collect usage

OpenHermit persists every turn to the `session_events` table; assistant rows carry the pi-ai `usage` blob in `payload->'usage'`:

```sql
SELECT payload::text
FROM session_events
WHERE agent_id = 'main'
  AND session_id = '<sid>'
  AND event_type = 'assistant'
ORDER BY id;
```

The runner sums `usage.input`, `usage.output`, `usage.cacheRead`, `usage.cacheWrite`, `usage.totalTokens`, and `usage.cost.total` across rows and writes the totals to `output/<...>/usage.json`.

### 8. Grade

`src/utils/grading.py:run_grading` is the grader driver. It:

1. Copies `src/utils/transcript_loader.py` into the container at `/tmp/_transcript_loader.py`.
2. Generates a tiny runner script that imports the task's `grade()` function, calls `load_transcript("postgres://session_events")`, then invokes `grade(transcript=_transcript, workspace_path="/tmp_workspace")` and prints the resulting dict as JSON.
3. Runs that script with `docker exec`, forwarding any keys listed in the task's `## Env` block as `-e KEY=value` (values pulled from the host env, never put on argv positionally).

The transcript loader, when handed `postgres://session_events`, runs `psql` inside the container and returns a list of dicts:

```
{ "ts": "...", "role": "<event_type>", "event_type": "<event_type>",
  "content": "...", "payload": { ... } }
```

Ordering is by `session_events.id` (insertion order).

### 9. Persist artefacts and tear down

After grading, `run_batch.py` calls:

- `collect_output_from_container` — `docker cp <task>:/tmp_workspace/. <out>/task_output/`
- `dump_postgres` — `pg_dump hermit` → `<out>/hermit_db.sql`
- `remove_container` — `docker rm -f <task>`

## Output layout

For each run:

```
output/
  <category>/
    <task_id>/
      <short_model>_<YYYYMMDD_HHMM>_<runid>/
        score.json        # what grade() returned (incl. overall_score)
        usage.json        # token + cost totals
        session.json      # sessionId + final SyncResponse
        gateway.log       # gateway stdout/stderr (when captured)
        agent.log         # per-task driver logs (when captured)
        hermit_db.sql     # pg_dump of the hermit database
        task_output/      # snapshot of /tmp_workspace at teardown
```

Per-category summaries land at `output/<category>/summary_<model>.json`; the global summary at `output/summary_all_<model>.json` includes per-task `usage.cost_usd` and `scores.overall_score`.

## Cost-vs-performance reporting

The global summary is the cost-vs-quality artefact. Each entry carries:

- `scores.overall_score` — produced by the task's `grade()`, in `[0, 1]`.
- `usage.cost_usd` — sum of `payload.usage.cost.total` across assistant turns.
- `usage.output_tokens`, `usage.input_tokens`, `usage.total_tokens`.

Compare models by running the same set of tasks against each model and diffing the two `summary_all_*.json` files. Higher `overall_score` at lower `cost_usd` wins.

## File map

| Path                                    | Role                                                |
|-----------------------------------------|-----------------------------------------------------|
| `eval/run_batch.py`                     | CLI entrypoint, parallel scheduler, output writer   |
| `src/agents/openhermit/runner.py`       | HTTP driver: session, message, usage extraction     |
| `src/utils/docker_utils.py`             | `docker run`/`exec`/`cp`/`port` wrappers            |
| `src/utils/task_parser.py`              | YAML frontmatter + `##` section parser              |
| `src/utils/grading.py`                  | In-container grader runner                          |
| `src/utils/transcript_loader.py`        | Postgres-or-file transcript loader (in-container)   |
| `docker/Dockerfile`                     | Ubuntu + Node + Bun + Postgres 16 + openhermit      |
| `docker/entrypoint.sh`                  | Postgres bootstrap, seed apply, `hermit gateway run`|
| `docker/seed_helpers.sh`                | Source-able helpers for `seed_post.sh`              |
| `docs/seed-format.md`                   | Seed block reference + verified schema columns      |
| `docs/designing-tasks.md`               | Task authoring guide                                |
