---
id: 05_Memory_Introspection_task_4_delete_on_request
name: Delete a long-term memory on request
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt

Forget my penicillin allergy — that was incorrect information. Please delete the existing long-term memory entry with key `fact-allergy` using the `memory_delete` tool, then reply with `DONE` and nothing else.

## Expected Behavior

The agent calls `memory_delete` with key `fact-allergy` and the row is removed from `memories`.

## Grading Criteria

- [ ] No row exists in `memories` for `(main, fact-allergy)`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"memory_deleted": 0.0, "overall_score": 0.0}
    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT count(*) FROM memories "
             "WHERE agent_id='main' AND memory_key='fact-allergy';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode != 0:
        return scores
    try:
        count = int(r.stdout.strip())
    except ValueError:
        return scores
    if count == 0:
        scores["memory_deleted"] = 1.0
    scores["overall_score"] = scores["memory_deleted"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_4_delete_on_request
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'fact-allergy', 'Alice is allergic to penicillin. This is critical.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO UPDATE SET content = EXCLUDED.content;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
