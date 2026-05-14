---
id: 06_Scheduling_Automation_task_2_one_shot
name: Create a one-shot reminder schedule
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

Create a one-time reminder for tomorrow at 09:00 UTC. Use the `schedule_create` tool with:

- `type`: `"once"`
- `run_at`: an ISO 8601 timestamp for tomorrow at 09:00 UTC (e.g. if today is 2026-05-15 then `"2026-05-16T09:00:00Z"`)
- `prompt`: `"Remind me to call mom."`
- `id`: `"call-mom"`

Call the tool exactly once. After it succeeds, reply with `DONE`. Do not list schedules first.

## Expected Behavior

A row in `schedules` for `(main, call-mom)` exists with `type='once'` and `run_at` between 22 and 26 hours in the future.

## Grading Criteria

- [ ] Row exists.
- [ ] `type='once'`, `status='active'`.
- [ ] `run_at` is within ±2 hours of tomorrow 09:00 UTC.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    from datetime import datetime, timedelta, timezone

    scores = {
        "row_exists": 0.0,
        "type_ok": 0.0,
        "run_at_in_window": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "|", "-c",
             "SELECT type, status, run_at FROM schedules "
             "WHERE agent_id='main' AND schedule_id='call-mom';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode != 0 or not r.stdout.strip():
        return scores
    parts = r.stdout.strip().split("|")
    if len(parts) < 3:
        return scores
    scores["row_exists"] = 1.0
    sched_type, status, run_at = parts[0], parts[1], parts[2]
    if sched_type == "once" and status == "active":
        scores["type_ok"] = 1.0

    # Expected: tomorrow 09:00 UTC. Accept ±2h slack to be robust to time-math
    # mistakes from weak models.
    now = datetime.now(timezone.utc)
    tomorrow_9 = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    try:
        # run_at format examples: "2026-05-16T09:00:00Z" or with offset.
        raw = run_at.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        actual = datetime.fromisoformat(raw)
        if actual.tzinfo is None:
            actual = actual.replace(tzinfo=timezone.utc)
        delta = abs((actual - tomorrow_9).total_seconds())
        if delta <= 2 * 3600:
            scores["run_at_in_window"] = 1.0
    except Exception:
        pass

    scores["overall_score"] = (
        scores["row_exists"]
        + scores["type_ok"]
        + scores["run_at_in_window"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_2_one_shot
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
