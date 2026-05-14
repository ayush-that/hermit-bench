---
id: 01_CLI_Fluency_task_5_schedule_pause
name: Pause a cron schedule
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

The cron schedule `daily-digest` on agent `main` should be paused while we debug it. Pause it now without deleting it.

You have shell access. The relevant command is:

```
hermit schedules pause daily-digest --agent main
```

When the schedule has been paused, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `schedules` row for `(main, daily-digest)` has `status='paused'`.

## Grading Criteria

- [ ] `SELECT status FROM schedules WHERE agent_id='main' AND schedule_id='daily-digest'` returns `paused`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"schedule_paused": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c",
             "SELECT status FROM schedules "
             "WHERE agent_id='main' AND schedule_id='daily-digest';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0:
        return scores

    if r.stdout.strip() == "paused":
        scores["schedule_paused"] = 1.0

    scores["overall_score"] = scores["schedule_paused"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_5_schedule_pause
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

# Insert an active daily-digest schedule directly. The gateway's CLI create
# command wraps the same insert; doing it in SQL keeps the seed deterministic.
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
