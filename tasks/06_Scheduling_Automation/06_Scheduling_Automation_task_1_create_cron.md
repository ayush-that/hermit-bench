---
id: 06_Scheduling_Automation_task_1_create_cron
name: Create a weekly cron schedule
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

Create a recurring cron schedule for this agent. Use the `schedule_create` tool with these exact arguments:

- `type`: `"cron"`
- `cron_expression`: `"0 17 * * FRI"` (every Friday at 17:00 UTC)
- `prompt`: `"Generate this week's release notes."`
- `id`: `"weekly-release-notes"`

Call the tool exactly once. After it succeeds, reply with `DONE`. Do not list schedules first — just create it.

## Expected Behavior

After the agent finishes, the `schedules` table contains a row with `agent_id='main'`, `schedule_id='weekly-release-notes'`, `type='cron'`, `status='active'`, and a Friday-17:00 cron expression.

## Grading Criteria

- [ ] Row exists for `(main, weekly-release-notes)`.
- [ ] Cron expression matches a Friday-17:00 pattern.
- [ ] Type is `cron` and status is `active`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess, re
    scores = {
        "row_exists": 0.0,
        "cron_correct": 0.0,
        "type_status_ok": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "|", "-c",
             "SELECT type, status, cron_expression FROM schedules "
             "WHERE agent_id='main' AND schedule_id='weekly-release-notes';"],
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
    sched_type, status, cron_expr = parts[0], parts[1], parts[2]
    if sched_type == "cron" and status == "active":
        scores["type_status_ok"] = 1.0
    # Accept "0 17 * * FRI" or "0 17 * * 5" (Fri=5) with optional whitespace.
    norm = re.sub(r"\s+", " ", cron_expr.strip()).upper()
    if norm in ("0 17 * * FRI", "0 17 * * 5"):
        scores["cron_correct"] = 1.0

    scores["overall_score"] = (
        scores["row_exists"]
        + scores["cron_correct"]
        + scores["type_status_ok"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_1_create_cron
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
