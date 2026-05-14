---
id: 05_Memory_Introspection_task_3_update_existing
name: Update an existing long-term memory
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt

I switched coffee preferences — please update what you remember. Use `memory_update` on the existing memory `fact-favorite-coffee` and set the content to `Alice prefers cortados, no foam.`. After it is updated, reply with `DONE` and nothing else.

## Expected Behavior

The agent calls `memory_update` on `fact-favorite-coffee` and the row's content now mentions `cortado`.

## Grading Criteria

- [ ] Memory row `(main, fact-favorite-coffee)` still exists.
- [ ] Its content contains `cortado` (case-insensitive).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"key_preserved": 0.0, "content_updated": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT content FROM memories "
             "WHERE agent_id='main' AND memory_key='fact-favorite-coffee';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode != 0:
        return scores
    content = (r.stdout or "").strip()
    if content:
        scores["key_preserved"] = 1.0
    if "cortado" in content.lower():
        scores["content_updated"] = 1.0
    scores["overall_score"] = (scores["key_preserved"] + scores["content_updated"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_3_update_existing
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'fact-favorite-coffee', 'Alice prefers oat-milk flat whites, no sugar.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO UPDATE SET content = EXCLUDED.content;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
