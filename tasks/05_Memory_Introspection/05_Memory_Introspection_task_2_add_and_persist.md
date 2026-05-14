---
id: 05_Memory_Introspection_task_2_add_and_persist
name: Add and persist a new long-term memory
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt

Please remember the following long-term: my work laptop's serial number is ZX-119-882. Save it now using the `memory_add` tool with `content` set to `My work laptop's serial number is ZX-119-882.` (use any reasonable key, e.g. `fact-work-laptop-serial`). Do not search existing memories first; I am giving you this fact fresh. After `memory_add` returns successfully, reply with `DONE` and nothing else.

## Expected Behavior

The agent calls `memory_add` (or `memory_update`) to insert a new row in `memories` whose content references the serial `ZX-119-882`.

## Grading Criteria

- [ ] A row exists in `memories` for `agent_id='main'` whose `content` contains `ZX-119-882`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"memory_persisted": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT count(*) FROM memories "
             "WHERE agent_id='main' AND content LIKE '%ZX-119-882%';"],
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
    if count >= 1:
        scores["memory_persisted"] = 1.0
    scores["overall_score"] = scores["memory_persisted"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_2_add_and_persist
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
```

## Env

```
OPENROUTER_API_KEY
```
