---
id: 05_Memory_Introspection_task_6_working_memory_summary
name: Update working memory with a session summary
category: 05_Memory_Introspection
timeout_seconds: 240
---

## Prompt

We've been chatting for a while now. Please summarize our conversation so far in exactly three short bullet points covering the main topics. Format each bullet on its own line starting with `- `. After the three bullets, reply with `DONE` on the final line.

## Expected Behavior

The `working_memory_update` tool is only available inside the introspection sub-agent — it is NOT in the main agent's toolset. As a simplification, we grade the agent's textual response instead: a correct response contains three bullet-prefixed lines summarising the conversation. (In a full integration test the harness would trigger `POST /api/agents/main/sessions/<sid>/checkpoint` after the user turn to invoke introspection; that path is left for a future task.)

## Grading Criteria

- [ ] The assistant's reply contains at least three lines starting with `- ` (markdown bullets).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"three_bullets": 0.0, "overall_score": 0.0}
    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT string_agg(content, '\n') FROM session_events "
             "WHERE agent_id='main' AND event_type='assistant' "
             "AND content IS NOT NULL;"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode != 0:
        return scores
    body = r.stdout or ""
    bullet_lines = [
        ln for ln in body.splitlines()
        if ln.lstrip().startswith("- ") or ln.lstrip().startswith("* ")
    ]
    if len(bullet_lines) >= 3:
        scores["three_bullets"] = 1.0
    scores["overall_score"] = scores["three_bullets"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_6_working_memory_summary
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
