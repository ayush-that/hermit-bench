---
id: 05_Memory_Introspection_task_7_introspection_idle_trigger
name: Idle-triggered introspection writes a memory
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt

We have a quiet moment between tasks. Before we continue, please run a brief self-introspection pass on this session so future-you has continuity: look at the conversation so far, decide whether anything is worth saving long-term, update your working memory if useful, and add a long-term memory entry summarising any durable fact you noticed. When you finish, reply with `DONE` and nothing else.

## Expected Behavior

We cannot wait the full 10-minute `idle_timeout_minutes` window in a benchmark run, so this task **simulates** an idle-triggered introspection: a synthetic `introspection_start` event is pre-seeded into `session_events` with `reason='idle'`. The grader checks that the seeded event exists AND that the agent took at least one memory-mutating action during the turn.

## Grading Criteria

- [ ] A seeded `introspection_start` row exists with `payload->>'reason' = 'idle'`.
- [ ] The agent invoked `memory_add`, `memory_update`, or `working_memory_update` at least once.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {
        "idle_event_seeded": 0.0,
        "memory_tool_used": 0.0,
        "overall_score": 0.0,
    }
    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT count(*) FROM session_events "
             "WHERE agent_id='main' AND event_type='introspection_start' "
             "AND payload->>'reason' = 'idle';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode == 0:
        try:
            if int(r.stdout.strip()) >= 1:
                scores["idle_event_seeded"] = 1.0
        except ValueError:
            pass

    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT count(*) FROM session_events "
             "WHERE agent_id='main' AND event_type='tool_call' "
             "AND payload->>'name' IN ('memory_add','memory_update','working_memory_update');"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode == 0:
        try:
            if int(r.stdout.strip()) >= 1:
                scores["memory_tool_used"] = 1.0
        except ValueError:
            pass

    scores["overall_score"] = (
        scores["idle_event_seeded"] + scores["memory_tool_used"]
    ) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_7_introspection_idle_trigger
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
# Simulate an idle-triggered introspection by pre-seeding a synthetic
# introspection_start event with reason='idle'. The real runtime would write
# this row after `memory.introspection.idle_timeout_minutes` of inactivity;
# the benchmark cannot wait 10+ minutes of wall-clock, so we inject it.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO session_events (agent_id, session_id, ts, event_type, payload, content, user_id)
VALUES (
  'main',
  'synthetic-idle-session',
  NOW()::text,
  'introspection_start',
  jsonb_build_object('ts', NOW()::text, 'role', 'system', 'type', 'introspection_start', 'reason', 'idle'),
  NULL,
  NULL
);
SQL
```

## Env

```
OPENROUTER_API_KEY
```
