# Seed format

Each HermitBench task can ship two seed blocks in its task `.md` file:

| Block         | When applied                          | What for |
|---------------|---------------------------------------|----------|
| `## Seed SQL` | Before the gateway boots              | Raw DB inserts — users, memories, instructions, `agent_policies`, schedules |
| `## Seed Post`| After the gateway responds on `/health` | `hermit ...` CLI calls that need a live gateway (agent create, secret set, skill register) |

The Python runner copies both blocks to the per-task workspace as `seed.sql` and `seed_post.sh`; the container's `entrypoint.sh` then picks them up automatically (see `docker/entrypoint.sh`).

## Postgres connection inside the container

```
host: 127.0.0.1
port: 5432
db:   hermit
user: hermit
pw:   hermit
```

Outside `seed_post.sh` you can also reach it from the grader: `PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1`.

## Table reference

The fixtures and `Seed SQL` blocks must match the OpenHermit Drizzle schema at `packages/store/src/schema.ts`. The columns most tasks touch:

| Table             | Primary key                | Required columns (besides PK)            | Notes |
|-------------------|----------------------------|------------------------------------------|-------|
| `users`           | `user_id`                  | `created_at`, `updated_at` (text)        | No `role` / `display_name` columns. |
| `user_identities` | `(channel, channel_user_id)` | `user_id`, `created_at`                | |
| `agents`          | `agent_id`                 | `workspace_dir`, `created_at`, `updated_at` | Prefer `hermit agents create` instead of raw INSERT. |
| `instructions`    | `(agent_id, key)`          | `content`, `updated_at`                  | `key` examples: `identity`, `soul`, `rules`. |
| `memories`        | `(agent_id, memory_key)`   | `content`, `updated_at`                  | The PK column is `memory_key`, not `key`. |
| `agent_skills`    | `(agent_id, skill_id)`     | `enabled`, `created_at`                  | Register skills with `hermit skills register` first. |
| `agent_policies`  | `id` (text)                | `agent_id`, `resource_type`, `resource_key`, `created_at`, `updated_at` | Table is `agent_policies`, not `access_policies`. |
| `schedules`       | `(agent_id, schedule_id)`  | `type`, `prompt`, `created_at`, `updated_at` | |
| `session_events`  | `id` (serial)              | `agent_id`, `session_id`, `ts`, `event_type`, `payload` | The grader reads `eventType = 'assistant'` rows to extract usage. |

Timestamp columns in the Drizzle schema are `text`, so cast `NOW()` to text inside SQL: `NOW()::text`.

## Sourceable seed helpers

Inside `seed_post.sh`, run `source /usr/local/bin/seed_helpers.sh` to use:

- `hb_seed_agent <id>` — idempotent `hermit agents create` + `enable`.
- `hb_seed_instruction <agent> <key> <content>` — `hermit instructions set --agent <a> <key> <content>`.
- `hb_seed_skill <agent> <skill_dir>` — `hermit skills register` then `enable --agent <a>`.
- `hb_seed_memory_via_sql <agent> <key> <content>` — `INSERT INTO memories (agent_id, memory_key, content, updated_at)`.
- `hb_seed_secret <agent> <key> <value>` — `hermit config --agent <a> secrets set <key> <value>`.
- `hb_seed_openrouter <agent> <api_key> <model>` — convenience: secret + `model.provider=openrouter` + `model.model=<m>`.

## CLI flag placement

- `hermit config` carries `--agent` as a **subcommand-level** option (i.e. `hermit config --agent <id> set ...` and `hermit config --agent <id> secrets set ...`). It is NOT a top-level flag on `hermit` itself.
- `hermit instructions set` takes `--agent` on the subcommand.
- `hermit skills register` is global, but `hermit skills enable` takes `--agent`.

## Bundled fixtures

- `fixtures/skills/standup-digest/SKILL.md` — register with `hb_seed_skill main fixtures/skills/standup-digest`.
