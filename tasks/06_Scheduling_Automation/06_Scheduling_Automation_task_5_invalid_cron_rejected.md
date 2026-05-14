---
id: 06_Scheduling_Automation_task_5_invalid_cron_rejected
name: Reject an invalid cron expression
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

The user wants you to create a cron schedule with the cron expression `at midnight`. That's not a valid cron expression. Do NOT call `schedule_create` with that expression — it will be rejected and there's no point trying. Instead, reply in plain text explaining that `at midnight` is not a valid cron expression and suggest a valid one (e.g. `0 0 * * *` for every day at midnight UTC). Make sure your reply contains the string `0 0 * * *`.

## Expected Behavior

No new rows in `schedules`. The assistant's final reply mentions that `at midnight` is invalid and proposes a valid cron expression.

## Grading Criteria

- [ ] No new schedule rows on agent `main`.
- [ ] Assistant final reply mentions a valid cron pattern like `0 0 * * *`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {
        "no_new_rows": 0.0,
        "suggests_valid": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    r = subprocess.run(
        ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
         "-At", "-c", "SELECT count(*) FROM schedules WHERE agent_id='main';"],
        capture_output=True, text=True, env=env, timeout=15,
    )
    try:
        n = int((r.stdout or "0").strip())
    except ValueError:
        n = -1
    if n == 0:
        scores["no_new_rows"] = 1.0

    # Pull final assistant reply text from transcript.
    reply = ""
    if isinstance(transcript, list):
        for ev in transcript:
            if not isinstance(ev, dict):
                continue
            role = ev.get("role") or ev.get("event_type") or ""
            if "assistant" in str(role).lower() or "assistant_message" in str(role).lower():
                content = ev.get("content") or ev.get("text") or ""
                if isinstance(content, str) and content.strip():
                    reply = content
    elif isinstance(transcript, str):
        reply = transcript
    if "0 0 * * *" in reply:
        scores["suggests_valid"] = 1.0

    scores["overall_score"] = (
        scores["no_new_rows"] + scores["suggests_valid"]
    ) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_5_invalid_cron_rejected
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
