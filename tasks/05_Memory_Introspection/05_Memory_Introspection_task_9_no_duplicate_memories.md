---
id: 05_Memory_Introspection_task_9_no_duplicate_memories
name: No duplicate memories on repeat fact
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt

Two pieces of info: first, my coffee preference is cortados. Second — I'm pretty sure I already told you my coffee preference at some point, right? Make sure your long-term memory has exactly ONE entry about my coffee preference (no duplicates). Use `memory_recall` or `memory_list` first to check existing entries, then either `memory_update` the existing row OR `memory_add` only if none exists. After you've finished, reply with `DONE` and nothing else.

## Expected Behavior

After the turn, there is exactly one memory row whose content references `cortado`. The agent should reuse the existing `fact-favorite-coffee` key rather than create a second row.

## Grading Criteria

- [ ] Exactly one memory row with `content` mentioning `cortado` (case-insensitive).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"single_coffee_memory": 0.0, "overall_score": 0.0}
    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT count(*) FROM memories "
             "WHERE agent_id='main' AND lower(content) LIKE '%cortado%';"],
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
    if count == 1:
        scores["single_coffee_memory"] = 1.0
    scores["overall_score"] = scores["single_coffee_memory"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_9_no_duplicate_memories
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
# Seed an existing coffee-preference memory so the agent has the choice of
# update vs add. The desired behaviour is to UPDATE in place, not duplicate.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'fact-favorite-coffee', 'Alice prefers oat-milk flat whites, no sugar.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO UPDATE
  SET content = EXCLUDED.content,
      updated_at = NOW()::text;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
