---
id: 01_CLI_Fluency_task_0_smoke
name: Health check
category: 01_CLI_Fluency
timeout_seconds: 120
---

## Prompt

Reply with exactly the single word `READY` and nothing else.

## Expected Behavior

The agent emits a single assistant turn whose content contains `READY`. No tool calls, no follow-up.

## Grading Criteria

- [ ] At least one assistant event in `session_events` whose `content` contains `READY`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    scores = {"replied_ready": 0.0, "overall_score": 0.0}
    if transcript:
        for msg in transcript:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role") or msg.get("event_type")
            if role != "assistant":
                continue
            content = msg.get("content") or ""
            if "READY" in content:
                scores["replied_ready"] = 1.0
                break
    scores["overall_score"] = scores["replied_ready"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_0_smoke
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
