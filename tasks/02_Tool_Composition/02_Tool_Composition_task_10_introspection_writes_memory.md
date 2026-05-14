---
id: 02_Tool_Composition_task_10_introspection_writes_memory
name: Save a salient user fact as a long-term memory
category: 02_Tool_Composition
timeout_seconds: 180
---

## Prompt

I'm about to share a fact about me. I will not repeat it, so please save it as a long-term memory using the `memory_add` tool so you can recall it in future sessions.

My favorite color is amethyst purple.

When you've saved the memory, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `memories` table has at least one row for `agent_id='main'` whose `content` mentions either `amethyst` or `purple` (case-insensitive). The agent should pick a sensible memory_key (e.g. `user/favorite_color` or similar).

## Grading Criteria

- [ ] At least one row in `memories` for `agent_id='main'`.
- [ ] At least one row's `content` contains `amethyst` or `purple`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"any_memory": 0.0, "color_recorded": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c",
             "SELECT content FROM memories WHERE agent_id='main';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode != 0:
        return scores

    contents = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if contents:
        scores["any_memory"] = 1.0
    blob = "\n".join(contents).lower()
    if "amethyst" in blob or "purple" in blob:
        scores["color_recorded"] = 1.0

    scores["overall_score"] = (scores["any_memory"] + scores["color_recorded"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_10_introspection_writes_memory
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
