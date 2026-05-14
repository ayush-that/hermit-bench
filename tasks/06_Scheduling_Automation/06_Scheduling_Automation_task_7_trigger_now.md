---
id: 06_Scheduling_Automation_task_7_trigger_now
name: Trigger a schedule immediately
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

The user wants to run the schedule `daily-digest` once right now without waiting for its next scheduled tick.

Use the `schedule_trigger` tool with `id`: `"daily-digest"`. Call it exactly once. After it succeeds, reply with `DONE`.

## Expected Behavior

The schedule's `last_run_at` advances to ~now (the `schedule_trigger` tool calls `markRun`). Alternatively the agent acknowledges the trigger in its reply (e.g. mentions "triggered" or "running"). Either signal is acceptable.

## Grading Criteria

- [ ] Either: `last_run_at` is within the last 60 minutes, OR the assistant reply confirms the schedule was triggered.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    from datetime import datetime, timezone, timedelta

    scores = {
        "trigger_signal": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    r = subprocess.run(
        ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
         "-At", "-c",
         "SELECT COALESCE(last_run_at, '') FROM schedules "
         "WHERE agent_id='main' AND schedule_id='daily-digest';"],
        capture_output=True, text=True, env=env, timeout=15,
    )
    last_run_recent = False
    raw = (r.stdout or "").strip()
    if raw:
        try:
            parsed = raw
            if parsed.endswith("Z"):
                parsed = parsed[:-1] + "+00:00"
            ts = datetime.fromisoformat(parsed)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - ts <= timedelta(hours=1):
                last_run_recent = True
        except Exception:
            pass

    # Fallback: scan transcript for an acknowledgement of the trigger.
    reply_blob = ""
    if isinstance(transcript, list):
        for ev in transcript:
            if not isinstance(ev, dict):
                continue
            for k in ("content", "text"):
                v = ev.get(k)
                if isinstance(v, str):
                    reply_blob += " " + v.lower()
    elif isinstance(transcript, str):
        reply_blob = transcript.lower()

    ack = any(kw in reply_blob for kw in ("triggered", "running now", "ran daily-digest",
                                          "scheduled to run", "executed daily-digest",
                                          "schedule_trigger"))

    if last_run_recent or ack:
        scores["trigger_signal"] = 1.0
    scores["overall_score"] = scores["trigger_signal"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_7_trigger_now
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
) ON CONFLICT (agent_id, schedule_id) DO UPDATE SET status = 'active', last_run_at = NULL;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
