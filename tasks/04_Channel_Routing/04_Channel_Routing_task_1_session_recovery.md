---
id: 04_Channel_Routing_task_1_session_recovery
name: Recover the latest message from an existing telegram session
category: 04_Channel_Routing
timeout_seconds: 240
---

## Prompt

A user on Telegram has been chatting with agent `main` in an existing session. The session id is `telegram:2026-05-14-aa11bb22`. Their last 5 messages live in the `session_events` table (event_type `user_message`).

Your job: look up that session's most recent user message and write its exact `content` to `/tmp_workspace/results/last_message.txt` (one line, no quotes, no extra text).

You have shell access. Useful tools:

- Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`.
- Query example: `psql -U hermit -d hermit -h 127.0.0.1 -At -c "SELECT content FROM session_events WHERE agent_id='main' AND session_id='telegram:2026-05-14-aa11bb22' AND event_type='user_message' ORDER BY id DESC LIMIT 1;"`

When the file has been written, reply with `DONE`.

## Expected Behavior

Channel adapters are not running in the test container; we simulate the telegram session by pre-seeding `sessions` + `session_events` rows directly. The agent should query Postgres for the most recent `user_message` content on the seeded session.

The expected fifth (latest) user message is:

```
Can you remind me what we decided about the Q3 launch?
```

## Grading Criteria

- [ ] `/tmp_workspace/results/last_message.txt` exists.
- [ ] File body equals the seeded latest user message (whitespace-trimmed match).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {"file_present": 0.0, "content_match": 0.0, "overall_score": 0.0}

    expected = "Can you remind me what we decided about the Q3 launch?"
    path = os.path.join(workspace_path, "results", "last_message.txt")
    if not os.path.isfile(path):
        return scores
    scores["file_present"] = 1.0

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read().strip()
    except OSError:
        return scores

    if body == expected:
        scores["content_match"] = 1.0
    elif expected in body:
        scores["content_match"] = 0.5

    scores["overall_score"] = (scores["file_present"] + scores["content_match"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_1_session_recovery
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

# Seed a simulated telegram session with 5 user_message events.
# The bridge would normally create this row when the first inbound arrives;
# we insert it directly because channel adapters are not running in the
# test container.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO sessions (
  agent_id, session_id, source_kind, source_platform, interactive,
  created_at, last_activity_at, message_count, completed_turn_count,
  status, type, user_ids, metadata
) VALUES (
  'main', 'telegram:2026-05-14-aa11bb22', 'channel', 'telegram', 1,
  '2026-05-14T10:00:00Z', '2026-05-14T10:30:00Z', 5, 0,
  'idle', 'direct', '["u_member"]'::jsonb,
  '{"telegram_chat_id":"55501","channel":"telegram"}'::jsonb
)
ON CONFLICT (agent_id, session_id) DO UPDATE SET
  metadata = EXCLUDED.metadata, last_activity_at = EXCLUDED.last_activity_at;

INSERT INTO session_events (agent_id, session_id, ts, event_type, payload, content, user_id) VALUES
  ('main', 'telegram:2026-05-14-aa11bb22', '2026-05-14T10:00:00Z', 'user_message',
   '{"sender":"u_member"}'::jsonb, 'hey, are you around?', 'u_member'),
  ('main', 'telegram:2026-05-14-aa11bb22', '2026-05-14T10:05:00Z', 'user_message',
   '{"sender":"u_member"}'::jsonb, 'I had a question about pricing', 'u_member'),
  ('main', 'telegram:2026-05-14-aa11bb22', '2026-05-14T10:15:00Z', 'user_message',
   '{"sender":"u_member"}'::jsonb, 'specifically the enterprise tier', 'u_member'),
  ('main', 'telegram:2026-05-14-aa11bb22', '2026-05-14T10:25:00Z', 'user_message',
   '{"sender":"u_member"}'::jsonb, 'also wanted to talk about onboarding', 'u_member'),
  ('main', 'telegram:2026-05-14-aa11bb22', '2026-05-14T10:30:00Z', 'user_message',
   '{"sender":"u_member"}'::jsonb, 'Can you remind me what we decided about the Q3 launch?', 'u_member');
SQL
```

## Env

```
OPENROUTER_API_KEY
```
