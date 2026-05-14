---
id: 04_Channel_Routing_task_9_session_summary_command
name: Summarize all recent telegram sessions
category: 04_Channel_Routing
timeout_seconds: 300
---

## Prompt

You are agent `main` and the owner just asked:

> Give me a summary of all sessions on telegram from the last 24h.

Build a summary at `/tmp_workspace/results/telegram_summary.txt`. The file must:

1. cite the session id of every telegram session whose `last_activity_at` is within the last 24 hours (there are three such sessions seeded — see below);
2. include one short, one-sentence summary line per session that mentions the topic from that session's most recent `user_message.content`.

Each line in the output must include both the session id and the topic text. Free-form prose is fine as long as both pieces appear together for each session.

You have shell access. Useful queries:

- list sessions: `SELECT session_id, last_activity_at FROM sessions WHERE agent_id='main' AND source_platform='telegram' AND last_activity_at > (NOW() - interval '24 hours')::text;`
- latest user message per session: `SELECT content FROM session_events WHERE agent_id='main' AND session_id=$1 AND event_type='user_message' ORDER BY id DESC LIMIT 1;`

Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`.

When the file is written, reply with `DONE`.

## Expected Behavior

Channel adapters are not running in the test container; three telegram sessions with distinct topics are seeded directly. The agent enumerates recent telegram sessions and produces a per-session summary that names the session id and references the topic.

## Grading Criteria

- [ ] File exists at `/tmp_workspace/results/telegram_summary.txt`.
- [ ] All three session ids appear in the file.
- [ ] All three topic keywords (`pricing`, `onboarding`, `roadmap`) appear in the file.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {
        "file_present": 0.0,
        "session_ids_present": 0.0,
        "topics_present": 0.0,
        "overall_score": 0.0,
    }

    path = os.path.join(workspace_path, "results", "telegram_summary.txt")
    if not os.path.isfile(path):
        return scores
    scores["file_present"] = 1.0

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
    except OSError:
        return scores

    expected_ids = [
        "telegram:2026-05-15-sumaa001",
        "telegram:2026-05-15-sumbb002",
        "telegram:2026-05-15-sumcc003",
    ]
    id_hits = sum(1 for sid in expected_ids if sid in body)
    scores["session_ids_present"] = id_hits / len(expected_ids)

    topics = ["pricing", "onboarding", "roadmap"]
    topic_hits = sum(1 for t in topics if t.lower() in body.lower())
    scores["topics_present"] = topic_hits / len(topics)

    scores["overall_score"] = (
        scores["file_present"]
        + scores["session_ids_present"]
        + scores["topics_present"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_9_session_summary_command
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
-- Three recent telegram sessions, each on a different topic.
INSERT INTO sessions (
  agent_id, session_id, source_kind, source_platform, interactive,
  created_at, last_activity_at, message_count, completed_turn_count,
  status, type, user_ids, metadata
) VALUES
  ('main', 'telegram:2026-05-15-sumaa001', 'channel', 'telegram', 1,
   (NOW() - interval '4 hours')::text, (NOW() - interval '4 hours')::text,
   1, 0, 'idle', 'direct', '["u_a"]'::jsonb,
   '{"telegram_chat_id":"1001","channel":"telegram"}'::jsonb),
  ('main', 'telegram:2026-05-15-sumbb002', 'channel', 'telegram', 1,
   (NOW() - interval '8 hours')::text, (NOW() - interval '8 hours')::text,
   1, 0, 'idle', 'direct', '["u_b"]'::jsonb,
   '{"telegram_chat_id":"1002","channel":"telegram"}'::jsonb),
  ('main', 'telegram:2026-05-15-sumcc003', 'channel', 'telegram', 1,
   (NOW() - interval '2 hours')::text, (NOW() - interval '2 hours')::text,
   1, 0, 'idle', 'direct', '["u_c"]'::jsonb,
   '{"telegram_chat_id":"1003","channel":"telegram"}'::jsonb)
ON CONFLICT (agent_id, session_id) DO UPDATE SET
  last_activity_at = EXCLUDED.last_activity_at,
  metadata = EXCLUDED.metadata;

INSERT INTO session_events (agent_id, session_id, ts, event_type, payload, content, user_id) VALUES
  ('main', 'telegram:2026-05-15-sumaa001',
   (NOW() - interval '4 hours')::text, 'user_message',
   '{}'::jsonb, 'can we revisit the pricing for the enterprise tier?', 'u_a'),
  ('main', 'telegram:2026-05-15-sumbb002',
   (NOW() - interval '8 hours')::text, 'user_message',
   '{}'::jsonb, 'need help with onboarding for the new hire', 'u_b'),
  ('main', 'telegram:2026-05-15-sumcc003',
   (NOW() - interval '2 hours')::text, 'user_message',
   '{}'::jsonb, 'where can I see the latest product roadmap?', 'u_c');

-- One older session that should NOT appear in the summary (last_activity > 24h ago).
INSERT INTO sessions (
  agent_id, session_id, source_kind, source_platform, interactive,
  created_at, last_activity_at, message_count, completed_turn_count,
  status, type, user_ids, metadata
) VALUES (
  'main', 'telegram:2026-05-10-oldold01', 'channel', 'telegram', 1,
  '2026-05-10T10:00:00Z', '2026-05-10T10:30:00Z', 1, 0,
  'idle', 'direct', '["u_x"]'::jsonb,
  '{"telegram_chat_id":"9999","channel":"telegram"}'::jsonb
)
ON CONFLICT (agent_id, session_id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
