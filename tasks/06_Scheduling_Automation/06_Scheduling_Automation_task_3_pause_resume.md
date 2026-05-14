---
id: 06_Scheduling_Automation_task_3_pause_resume
name: Pause now, schedule a resume in 48h
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

The schedule `daily-digest` on this agent is misbehaving and needs to be paused for two days. Do two things:

1. Use the `schedule_update` tool to set `daily-digest` to status `"paused"` immediately.
2. Use the `schedule_create` tool to create a one-shot schedule that resumes it. Use:
   - `type`: `"once"`
   - `run_at`: ISO 8601 timestamp 48 hours from now
   - `prompt`: `"Resume the daily-digest schedule by setting it back to active."`
   - `id`: `"resume-daily-digest"`

When both tool calls have succeeded, reply with `DONE`.

## Expected Behavior

`daily-digest` row has `status='paused'`. A new `resume-daily-digest` one-shot row exists with `run_at` ~48h ahead.

## Grading Criteria

- [ ] `daily-digest` is paused.
- [ ] `resume-daily-digest` exists with `type='once'` and `run_at` within ±2h of now+48h.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    from datetime import datetime, timedelta, timezone

    scores = {
        "paused": 0.0,
        "resume_one_shot": 0.0,
        "resume_when_ok": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "|", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    if q("SELECT status FROM schedules WHERE agent_id='main' "
         "AND schedule_id='daily-digest';") == "paused":
        scores["paused"] = 1.0

    row = q("SELECT type, run_at FROM schedules WHERE agent_id='main' "
            "AND schedule_id='resume-daily-digest';")
    if row and "|" in row:
        sched_type, run_at = row.split("|", 1)
        if sched_type == "once":
            scores["resume_one_shot"] = 1.0
        try:
            raw = run_at.strip()
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            actual = datetime.fromisoformat(raw)
            if actual.tzinfo is None:
                actual = actual.replace(tzinfo=timezone.utc)
            expected = datetime.now(timezone.utc) + timedelta(hours=48)
            if abs((actual - expected).total_seconds()) <= 2 * 3600:
                scores["resume_when_ok"] = 1.0
        except Exception:
            pass

    scores["overall_score"] = (
        scores["paused"]
        + scores["resume_one_shot"]
        + scores["resume_when_ok"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_3_pause_resume
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO schedules (
  agent_id, schedule_id, type, status, cron_expression, prompt,
  session_mode, delivery, policy, created_at, updated_at, run_count, consecutive_errors
) VALUES (
  'main', 'daily-digest', 'cron', 'active', '0 9 * * *',
  'Produce the daily digest.',
  'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb,
  NOW()::text, NOW()::text, 0, 0
) ON CONFLICT (agent_id, schedule_id) DO UPDATE SET status = 'active';
SQL
```

## Env

```
OPENROUTER_API_KEY
```
