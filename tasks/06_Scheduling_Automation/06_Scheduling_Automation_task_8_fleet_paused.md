---
id: 06_Scheduling_Automation_task_8_fleet_paused
name: Pause every cron schedule on this agent
category: 06_Scheduling_Automation
timeout_seconds: 300
---

## Prompt

A maintenance window is starting. Pause every cron schedule on this agent. There are three: `digest-am`, `digest-pm`, and `weekly-report`.

For each one, use the `schedule_update` tool with `status`: `"paused"`. Make three tool calls total, one per schedule id. After all three succeed, reply with `DONE`.

## Expected Behavior

All three cron schedules on agent `main` have `status='paused'`.

## Grading Criteria

- [ ] All cron-type schedules on `main` have `status='paused'`.
- [ ] Total count of paused cron schedules on `main` is 3 (or more).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {
        "all_paused": 0.0,
        "count_ok": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    non_paused = q(
        "SELECT count(*) FROM schedules "
        "WHERE agent_id='main' AND type='cron' AND status <> 'paused';"
    )
    paused = q(
        "SELECT count(*) FROM schedules "
        "WHERE agent_id='main' AND type='cron' AND status='paused';"
    )
    try:
        if int(non_paused or "1") == 0:
            scores["all_paused"] = 1.0
    except ValueError:
        pass
    try:
        if int(paused or "0") >= 3:
            scores["count_ok"] = 1.0
    except ValueError:
        pass

    scores["overall_score"] = (
        scores["all_paused"] + scores["count_ok"]
    ) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_8_fleet_paused
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO schedules (
  agent_id, schedule_id, type, status, cron_expression, prompt,
  session_mode, delivery, policy, created_at, updated_at, run_count, consecutive_errors
) VALUES
  ('main', 'digest-am',     'cron', 'active', '0 9 * * *',  'Morning digest.',
    'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb, NOW()::text, NOW()::text, 0, 0),
  ('main', 'digest-pm',     'cron', 'active', '0 18 * * *', 'Evening digest.',
    'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb, NOW()::text, NOW()::text, 0, 0),
  ('main', 'weekly-report', 'cron', 'active', '0 9 * * MON','Weekly report.',
    'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb, NOW()::text, NOW()::text, 0, 0)
ON CONFLICT (agent_id, schedule_id) DO UPDATE SET status = 'active';
SQL
```

## Env

```
OPENROUTER_API_KEY
```
