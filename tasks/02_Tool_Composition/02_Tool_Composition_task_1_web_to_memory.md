---
id: 02_Tool_Composition_task_1_web_to_memory
name: Fetch a page and store its title as a long-term memory
category: 02_Tool_Composition
timeout_seconds: 300
---

## Prompt

Fetch the page at `https://example.com` using the `web_fetch` tool and store the page's title (e.g. `Example Domain`) under a long-term memory whose key is `web-example-title`. Use the `memory_add` tool with `key="web-example-title"` and the page title as the `content`.

When the memory has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `memories` table has a row with `agent_id='main'` and `memory_key='web-example-title'` whose `content` contains the literal phrase `Example Domain` (the title of https://example.com).

## Grading Criteria

- [ ] A row exists in `memories` with `agent_id='main'` and `memory_key='web-example-title'`.
- [ ] That row's `content` contains the case-insensitive substring `example domain`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"memory_exists": 0.0, "title_match": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c",
             "SELECT content FROM memories "
             "WHERE agent_id='main' AND memory_key='web-example-title';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0:
        return scores

    content = r.stdout.strip()
    if content:
        scores["memory_exists"] = 1.0
    if "example domain" in content.lower():
        scores["title_match"] = 1.0

    scores["overall_score"] = (scores["memory_exists"] + scores["title_match"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_1_web_to_memory
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
