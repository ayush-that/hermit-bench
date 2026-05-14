---
id: 04_Channel_Routing_task_5_cross_channel_identity
name: Recover a URL from another channel via cross-channel identity
category: 04_Channel_Routing
timeout_seconds: 240
---

## Prompt

You are agent `main`. A user (`u_member`) is chatting with you on Slack right now. They ask:

> Have I asked you about the launch on the web before? If yes, paste the link I shared.

The same user (`u_member`) has identities on both `slack` and `web` (see the `user_identities` table). Their `web` session is in the `sessions` table with `source_platform='web'`, and the URL they shared lives in a `user_message` event on that web session.

Look up that URL and write it to `/tmp_workspace/results/url.txt` (one line, no quotes, no extra text).

Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`.

When the file has been written, reply with `DONE`.

## Expected Behavior

Channel adapters are not running in the test container; both the slack session (current) and the web session (historical) are seeded directly. The agent should:

1. find that `u_member` has a `web` identity in `user_identities`,
2. find sessions on web that involve `u_member` (or scan `session_events` for the URL),
3. extract the URL `https://amiko.example.com/launch/q3` from the web session's user_message events,
4. write that URL to `/tmp_workspace/results/url.txt`.

## Grading Criteria

- [ ] `/tmp_workspace/results/url.txt` exists.
- [ ] File body equals (after trim) `https://amiko.example.com/launch/q3`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {"file_present": 0.0, "url_match": 0.0, "overall_score": 0.0}

    expected = "https://amiko.example.com/launch/q3"
    path = os.path.join(workspace_path, "results", "url.txt")
    if not os.path.isfile(path):
        return scores
    scores["file_present"] = 1.0

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read().strip()
    except OSError:
        return scores

    if body == expected:
        scores["url_match"] = 1.0
    elif expected in body:
        scores["url_match"] = 0.5

    scores["overall_score"] = (scores["file_present"] + scores["url_match"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_5_cross_channel_identity
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_member', 'Member', NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_agents (user_id, agent_id, role, created_at) VALUES
  ('u_member', 'main', 'member', NOW()::text)
ON CONFLICT (user_id, agent_id) DO UPDATE SET role = EXCLUDED.role;

-- u_member is reachable on both Slack and the web app.
INSERT INTO user_identities (user_id, channel, channel_user_id, created_at) VALUES
  ('u_member', 'slack', 'U02BOB',         NOW()::text),
  ('u_member', 'web',   'web-u_member-1', NOW()::text)
ON CONFLICT (channel, channel_user_id) DO NOTHING;

-- Current slack session (simulated, no live adapter).
INSERT INTO sessions (
  agent_id, session_id, source_kind, source_platform, interactive,
  created_at, last_activity_at, message_count, completed_turn_count,
  status, type, user_ids, metadata
) VALUES (
  'main', 'slack:2026-05-15-current0', 'channel', 'slack', 1,
  '2026-05-15T09:00:00Z', '2026-05-15T09:30:00Z', 1, 0,
  'running', 'direct', '["u_member"]'::jsonb,
  '{"slack_channel_id":"D0SLACK1","channel":"slack"}'::jsonb
)
ON CONFLICT (agent_id, session_id) DO UPDATE SET metadata = EXCLUDED.metadata;

-- Past web session with the URL the user shared.
INSERT INTO sessions (
  agent_id, session_id, source_kind, source_platform, interactive,
  created_at, last_activity_at, message_count, completed_turn_count,
  status, type, user_ids, metadata
) VALUES (
  'main', 'web:2026-05-10-history0', 'web', 'web', 1,
  '2026-05-10T12:00:00Z', '2026-05-10T12:05:00Z', 2, 1,
  'idle', 'direct', '["u_member"]'::jsonb,
  '{"channel":"web"}'::jsonb
)
ON CONFLICT (agent_id, session_id) DO UPDATE SET metadata = EXCLUDED.metadata;

INSERT INTO session_events (agent_id, session_id, ts, event_type, payload, content, user_id) VALUES
  ('main', 'web:2026-05-10-history0', '2026-05-10T12:00:00Z', 'user_message',
   '{"sender":"u_member"}'::jsonb,
   'check this out for the launch: https://amiko.example.com/launch/q3',
   'u_member'),
  ('main', 'web:2026-05-10-history0', '2026-05-10T12:00:30Z', 'assistant_message',
   '{}'::jsonb, 'got it, will review.', NULL);
SQL
```

## Env

```
OPENROUTER_API_KEY
```
