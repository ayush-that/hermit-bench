---
id: 06_Scheduling_Automation_task_6_delete_schedule
name: Delete a stale schedule
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

The schedule `stale-job` on this agent is no longer needed. Delete it permanently.

Use the `schedule_delete` tool with `id`: `"stale-job"`. Call it exactly once. After it succeeds, reply with `DONE`.

## Expected Behavior

The `(main, stale-job)` row is removed from `schedules`. No row remains.

## Grading Criteria

- [ ] `SELECT count(*) FROM schedules WHERE agent_id='main' AND schedule_id='stale-job'` returns 0.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"deleted": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    r = subprocess.run(
        ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
         "-At", "-c",
         "SELECT count(*) FROM schedules "
         "WHERE agent_id='main' AND schedule_id='stale-job';"],
        capture_output=True, text=True, env=env, timeout=15,
    )
    if r.returncode == 0 and (r.stdout or "").strip() == "0":
        scores["deleted"] = 1.0
    scores["overall_score"] = scores["deleted"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_6_delete_schedule
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
  'main', 'stale-job', 'cron', 'active', '0 3 * * *',
  'A stale job that nobody needs anymore.',
  'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb,
  NOW()::text, NOW()::text, 0, 0
) ON CONFLICT (agent_id, schedule_id) DO UPDATE SET status = 'active';
SQL
```

## Env

```
OPENROUTER_API_KEY
```
