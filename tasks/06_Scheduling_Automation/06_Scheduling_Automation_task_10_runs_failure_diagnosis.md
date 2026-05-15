---
id: 06_Scheduling_Automation_task_10_runs_failure_diagnosis
name: Diagnose why a schedule keeps failing
category: 06_Scheduling_Automation
timeout_seconds: 300
---

## Prompt

The schedule `weekly-release-notes` has been failing. Find out why.

1. Use the `schedule_runs` tool with `id`: `"weekly-release-notes"` and `limit`: `5`. Look at the `error` field of failed runs.
2. Reply with a short paragraph summarising the common error. Your reply MUST quote the actual error string from the runs (verbatim, at least one of the recurring error tokens).

There is no need to write any files. Reply when done.

## Expected Behavior

The assistant calls `schedule_runs`, reads the seeded `error` messages (all three failed runs share the substring `RATE_LIMIT_429`), and includes that exact token in its summary reply.

## Grading Criteria

- [ ] Assistant final reply contains the recurring error token `RATE_LIMIT_429`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    scores = {"cites_error": 0.0, "overall_score": 0.0}

    blob = ""
    if isinstance(transcript, list):
        for ev in transcript:
            if not isinstance(ev, dict):
                continue
            for k in ("content", "text"):
                v = ev.get(k)
                if isinstance(v, str):
                    blob += " " + v
            # tool results sometimes live under payload
            payload = ev.get("payload")
            if isinstance(payload, dict):
                for v in payload.values():
                    if isinstance(v, str):
                        blob += " " + v
    elif isinstance(transcript, str):
        blob = transcript

    if "RATE_LIMIT_429" in blob:
        scores["cites_error"] = 1.0
    scores["overall_score"] = scores["cites_error"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_10_runs_failure_diagnosis
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO schedules (
  agent_id, schedule_id, type, status, cron_expression, prompt,
  session_mode, delivery, policy, created_at, updated_at, run_count, consecutive_errors,
  last_error
) VALUES (
  'main', 'weekly-release-notes', 'cron', 'active', '0 17 * * FRI',
  'Generate this week''s release notes.',
  'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb,
  NOW()::text, NOW()::text, 3, 3,
  'OpenRouter call failed: RATE_LIMIT_429 (provider returned status 429)'
) ON CONFLICT (agent_id, schedule_id) DO UPDATE SET
  status = 'active',
  consecutive_errors = 3,
  last_error = EXCLUDED.last_error;

INSERT INTO schedule_runs (agent_id, schedule_id, status, prompt, started_at, finished_at, duration_ms, error)
VALUES
  ('main', 'weekly-release-notes', 'failed', 'gen', (NOW() - INTERVAL '3 hours')::text, (NOW() - INTERVAL '3 hours')::text, 800,
   'OpenRouter call failed: RATE_LIMIT_429 (provider returned status 429)'),
  ('main', 'weekly-release-notes', 'failed', 'gen', (NOW() - INTERVAL '2 hours')::text, (NOW() - INTERVAL '2 hours')::text, 900,
   'OpenRouter call failed: RATE_LIMIT_429 (provider returned status 429)'),
  ('main', 'weekly-release-notes', 'failed', 'gen', (NOW() - INTERVAL '1 hour')::text,   (NOW() - INTERVAL '1 hour')::text,   1100,
   'OpenRouter call failed: RATE_LIMIT_429 (provider returned status 429)');
SQL
```

## Env

```
OPENROUTER_API_KEY
```
