# Designing a HermitBench task

A HermitBench task is a single Markdown file under `tasks/<category>/` that:

- Prompts the agent once.
- Seeds whatever Postgres state and gateway config the prompt needs.
- Provides a Python `grade()` function that the harness runs inside the container after the agent finishes.

This guide covers what makes a task good, how the seed/grading contracts work, and the pitfalls that bite in practice.

## What makes a good task

1. **Single, narrow objective.** "Create a schedule named `daily-standup` that runs at 09:00 UTC" beats "make the agent better at scheduling." One sentence, one outcome.
2. **Deterministic ground truth.** Score from durable state — a DB row, a file on disk, a memory key — not from prose phrasing. Reserve fuzzy text checks for tasks that are explicitly about generated content.
3. **Hermit-specific.** If the same prompt could be evaluated against vanilla `gpt-4o-mini` without a hermit gateway, it doesn't belong here. Lean on what hermit uniquely exposes: agents, channels, memories, instructions, policies, schedules, skills.
4. **Bounded timeout.** `timeout_seconds` in the frontmatter caps the gateway-side `?wait=true` window. Default to 120–180s; only go higher when the task genuinely needs long-horizon tool use.
5. **Minimal seed.** Don't `\i` the entire fixture set. Seed only the rows the prompt and grader touch — extraneous rows make failures harder to read and increase the surface area for accidental coupling between tasks.
6. **Self-contained grader.** The grader runs inside an ephemeral container against a one-shot DB. Don't depend on out-of-band state, network calls, or files the seed didn't create.

## File anatomy

```markdown
---
id: 05_Memory_Introspection_task_1_recall_existing
name: Recall an existing long-term memory
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt
<single user message>

## Expected Behavior
<plain-English what the agent should do — for humans, not the grader>

## Grading Criteria
- [ ] checkbox-style rubric for humans

## Automated Checks
```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    ...
```

## Workspace Path
```
fixtures/workspaces/05_Memory_Introspection/task_1_recall_existing
```

## Seed SQL
```sql
-- runs BEFORE gateway boot, against an empty hermit DB
```

## Seed Post
```bash
# runs AFTER /health is ready; can use the hermit CLI
```

## Env
```
OPENROUTER_API_KEY
```
```

Field rules:

- The file **must** open with `---`-delimited YAML frontmatter. `id` and `timeout_seconds` are read from there; everything else is parsed from `## ` headings.
- `## Workspace Path` is **required**. It may be a relative path; the parser resolves it against the repo root.
- All other sections are optional, but `## Automated Checks` is what produces a score — if you omit it, the run reports no scores.
- Section bodies wrapped in triple backticks are stripped (the parser removes the fences and the language tag).

## Seed contract

There are two seed slots; pick the right one. See also `docs/seed-format.md` for the full schema reference.

### `## Seed SQL` — pre-gateway

- Applied by `entrypoint.sh` with `psql -U hermit -d hermit -f /tmp_workspace/seed.sql` **before** `hermit gateway run` starts.
- The DB at this point contains only what Postgres ships with — the OpenHermit Drizzle migrations have **not run yet**. So `Seed SQL` can only insert into tables that exist pre-migration (in practice: very few). Use it sparingly; most state setup belongs in `Seed Post`.

### `## Seed Post` — post-gateway

- Written to `/tmp_workspace/seed_post.sh` and executed via `bash` once `/health` responds.
- This is where `hermit agents create`, `hermit instructions set`, `hermit skills register`, `hermit config secrets set`, and most `INSERT INTO memories` calls belong. The migrations have run, so the full schema is available.
- Source the helpers at the top: `source /usr/local/bin/seed_helpers.sh`. Then use `hb_seed_agent`, `hb_seed_instruction`, `hb_seed_skill`, `hb_seed_memory_via_sql`, `hb_seed_secret`, `hb_seed_openrouter`.

### Schema gotchas

These have all bitten real tasks:

- `memories` PK is `(agent_id, memory_key)`, **not** `key`.
- The table for ACL rows is `agent_policies`, **not** `access_policies`.
- `users` has no `role` or `display_name` columns.
- Timestamp columns in the Drizzle schema are `text`. Cast: `NOW()::text`.
- `hermit config` takes `--agent` on the `config` subcommand itself, not on `set` / `secrets set` and not on top-level `hermit`.

## Grader contract

The harness builds and runs (in `src/utils/grading.py`):

```python
import json
from _transcript_loader import load_transcript
_transcript = load_transcript("postgres://session_events")

# --- your ## Automated Checks block is inlined here ---

result = grade(transcript=_transcript, workspace_path="/tmp_workspace")
print(json.dumps(result))
```

### Signature

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    ...
```

Use both parameters as keyword arguments. The harness always passes them by keyword.

### Transcript shape

`transcript` is a list of dicts, oldest first, ordered by `session_events.id`:

```python
{
    "ts": "2026-05-15T17:10:42.123Z",   # text
    "role": "<event_type>",              # alias of event_type for convenience
    "event_type": "user" | "assistant" | "tool_call" | "tool_result" | ...,
    "content": "<text content, may be empty>",
    "payload": { ... },                  # full event payload (incl. usage on assistant rows)
}
```

For prose checks, iterate and filter on `msg.get("role") == "assistant"`. For tool-use checks, look for `event_type == "tool_call"` and inspect `payload`.

### Workspace

Cwd inside the grader container is `/tmp_workspace` (the same dir that was bind-mounted into the agent's container). Files the agent wrote during its run are visible here. The grader can also reach Postgres directly:

```python
import subprocess
r = subprocess.run(
    ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1", "-At", "-c",
     "SELECT count(*) FROM memories WHERE agent_id='main';"],
    capture_output=True, text=True, env={"PGPASSWORD": "hermit"},
)
```

### Return shape

`grade()` must return a `dict` with at minimum:

```python
{
    "overall_score": 0.75,        # float in [0, 1] — the primary headline number
    # any number of sub-scores, each a float in [0, 1]
    "checked_something":     1.0,
    "did_not_leak_secret":   1.0,
    "answered_in_one_turn":  0.5,
}
```

`overall_score` is what `summary_all_<model>.json` rolls up and what the per-task headline reports. Sub-scores are written to `score.json` but only `overall_score` flows into the global cost-vs-performance table. If you omit `overall_score`, the summary falls back to the mean of all numeric values — explicit is better.

Non-numeric keys (e.g. `"error": "..."`) are preserved but ignored by the aggregator.

### Env injection

If your grader needs an API key (e.g. for an LLM-as-judge call) or any host env var, list its name in `## Env`. The harness forwards `-e <NAME>=<value>` from the host environment into the grader's `docker exec`. Never put secrets in the task file itself.

### Judge-based grading

For tasks where the correct answer is a piece of prose (drafted post, DM reply, comment voice) deterministic regex checks can't grade quality. The harness exposes `judge(...)` inside the grader container so you can call an LLM-as-judge:

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    from _judge import judge, last_assistant_content

    # Pull the last assistant message. Prefer the transcript, but fall back
    # to last_assistant_content() — the default loader can drop multi-line
    # assistant replies because it splits psql output on newlines.
    last_assistant = ""
    if transcript:
        for msg in transcript:
            if (msg.get("role") or msg.get("event_type")) == "assistant":
                if (msg.get("content") or "").strip():
                    last_assistant = msg["content"]
    if not last_assistant:
        last_assistant = last_assistant_content().strip()
    if not last_assistant:
        return {"overall_score": 0.0, "error": "no assistant output"}

    rubric = {
        # name -> one-line description of what scores 1.0
        "length_60_to_120_words":   "the post is 60-120 words inclusive",
        "voice_match_lowercase":    "reads lowercase, short sentences, no emojis",
        "captures_original_thought":"the post is clearly about roadmaps being wishlists",
        "no_cliches":               "no LinkedIn-cliche phrases ('at the end of the day' etc.)",
        "no_preamble_or_quotes":    "the response is the post body only",
    }

    result = judge(
        task_prompt="Draft a 60-120 word post in the user's voice ...",
        agent_output=last_assistant,
        rubric=rubric,
        context="Voice samples: ...\nStyle: lowercase, short, no emojis.",
    )

    out = dict(result.get("rubric_scores") or {})
    out["overall_score"] = float(result.get("overall_score", 0.0))
    out["judge_reasoning"] = result.get("reasoning", "")
    out["judge_cost_usd"] = float((result.get("judge_usage") or {}).get("cost_usd", 0.0))
    return out
```

The judge model is read from `JUDGE_MODEL` (default `anthropic/claude-opus-4.7`); the API key from `OPENROUTER_API_KEY`. Both must be declared in `## Env` so the harness forwards them into the grader container:

```
## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
```

Rubric design rules:

- **Specific and falsifiable.** "Is this good?" is bad; "stays under 280 chars" is good; "does not use the phrase 'great post!'" is good.
- **3-6 criteria.** Fewer than 3 and a single bad judgement dominates the score; more than 6 and the judge stops attending to each one.
- **One criterion per axis.** Don't combine length and tone into a single bullet — judge separately so a failure is diagnosable.
- **Hard gates where appropriate.** If leaking a specific number ($182,000) is a strict policy violation, add a Python check that hard-zeros the "did_not_leak" criterion when the regex matches the number verbatim — don't rely solely on the judge.

The judge never raises. On network/parse error you get `{"overall_score": 0.0, "error": "...", "judge_model": ..., "judge_usage": {}}`, so your grader can always return numeric scores.

## Workspace fixtures

`## Workspace Path` points at a host directory that gets bind-mounted at `/tmp_workspace`. Use it for:

- Pre-existing files the agent should edit (a config, a log to tail, etc.).
- Reference data the grader will diff against (`expected.json`, golden outputs).

The directory must exist when the run starts. Empty is fine — `OpenHermitAgent.run_task` creates it if missing — but pre-seed it when the prompt assumes specific files.

## Common pitfalls

- **Seeding the wrong slot.** If a `Seed SQL` block fails with `relation "memories" does not exist`, move it to `Seed Post` — the migrations haven't run yet pre-gateway. See `tasks/05_Memory_Introspection/05_Memory_Introspection_task_1_recall_existing.md` for the canonical pattern.
- **Grading the wrong thing.** A grader that only checks `transcript` is blind to whatever the agent wrote to `/tmp_workspace` or to Postgres. For tasks about persistence (memories, schedules, instructions), query Postgres in the grader; the transcript only tells you what the model *said*, not what actually got written.
- **`?wait=true` timeout.** The gateway returns HTTP 504 with a `SyncResponse` body if the agent exceeds `timeout_seconds`. The runner records this as `error` on the execution but **still grades** — so make sure your grader handles "agent never finished" gracefully (return `overall_score: 0.0` rather than raising).
- **OpenRouter rate limits.** When benchmarking small free-tier models, keep `--parallel` low (1 or 2). Hitting 429 mid-run shows up as `error: post_message: 504 timeout` and tanks scores for reasons that have nothing to do with the model.
- **Working vs. long-term memory.** Working memory (the gateway's `session_events` for the current session) resets when the session ends; long-term memory (the `memories` table) persists. Grade persistence-style tasks by querying `memories`, not by inspecting the transcript.
- **Cron timing.** For schedule-trigger tasks, use the `hermit schedules trigger` CLI from the grader or from `seed_post.sh` instead of waiting on wall clock — the run is too short for real cron firings.
- **Secrets on argv.** Don't put `OPENROUTER_API_KEY=sk-...` literally in a seed block. List the key name in `## Env`; the harness forwards the value from the host environment so it never ends up in the task file or in `docker inspect`.
- **Idempotency.** Tasks share a Postgres image across runs of the same `task_id` — but containers are removed at teardown, so the next run starts clean. Don't rely on cross-run state.

## Verifying a new task locally

```bash
# Build the image once (or rebuild after Dockerfile changes).
docker build -t hermitbench-ubuntu:v0.1 -f docker/Dockerfile .

# Run just your task.
python eval/run_batch.py \
    --task tasks/<category>/<task_id>.md \
    --model openai/gpt-4o-mini \
    --parallel 1
```

Then inspect:

- `output/<category>/<task_id>/<short_model>_<ts>_<runid>/score.json` — what `grade()` returned.
- `output/.../hermit_db.sql` — full DB snapshot at teardown; useful for asserting your seed landed.
- `output/.../task_output/` — files the agent wrote to `/tmp_workspace`.
- `output/.../session.json` — final `SyncResponse` (sessionId, text, toolCalls, error).

If `score.json` carries `"error": "..."` instead of numeric scores, the grader itself crashed — fix it and rerun.
