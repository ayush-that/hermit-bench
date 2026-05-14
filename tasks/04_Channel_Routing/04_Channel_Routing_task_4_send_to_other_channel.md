---
id: 04_Channel_Routing_task_4_send_to_other_channel
name: Record an outbound Slack DM via the mock outbound queue
category: 04_Channel_Routing
timeout_seconds: 240
---

## Prompt

You are agent `main` on a CLI session with the owner. The owner asks:

> Send a slack DM to user `u_member` saying `standup at 10`.

In production, you would call the `session_send` tool which dispatches through the Slack adapter. The Slack adapter is not running in this test container — instead, a mock outbound queue table named `mock_outbound` is available in Postgres so we can record what would have been sent.

Schema of `mock_outbound`:

```
agent_id        text       -- e.g. 'main'
channel         text       -- 'telegram' | 'discord' | 'slack'
to_channel_id   text       -- slack channel id of the DM destination
body            text       -- the message text
created_at      text
```

`u_member` is linked to Slack user id `U02BOB` (see `user_identities` table). Record the outbound DM by inserting one row into `mock_outbound` with:

- `agent_id = 'main'`
- `channel = 'slack'`
- `to_channel_id = 'U02BOB'`
- `body = 'standup at 10'`

Postgres is at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`.

When the row has been inserted, reply with `DONE`.

## Expected Behavior

Channel adapters are not live in this container. The mock_outbound table simulates the Slack adapter's outbound delivery. The agent should resolve `u_member -> U02BOB` (either by querying `user_identities` or by trusting the prompt hint) and insert the outbound row.

## Grading Criteria

- [ ] `mock_outbound` contains exactly one row matching `(channel='slack', to_channel_id='U02BOB', body='standup at 10')`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"outbound_recorded": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c",
             "SELECT count(*) FROM mock_outbound "
             "WHERE agent_id='main' AND channel='slack' "
             "AND to_channel_id='U02BOB' AND body='standup at 10';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0:
        return scores

    count = r.stdout.strip()
    if count == "1":
        scores["outbound_recorded"] = 1.0

    scores["overall_score"] = scores["outbound_recorded"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_4_send_to_other_channel
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
-- Mock outbound queue simulates the Slack/Telegram/Discord adapter delivery.
CREATE TABLE IF NOT EXISTS mock_outbound (
  id            serial PRIMARY KEY,
  agent_id      text NOT NULL,
  channel       text NOT NULL,
  to_channel_id text NOT NULL,
  body          text NOT NULL,
  created_at    text NOT NULL DEFAULT NOW()::text
);

-- Seed users + identities so the agent can resolve u_member -> U02BOB.
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_owner',  'Owner',  NOW()::text, NOW()::text),
  ('u_member', 'Member', NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_agents (user_id, agent_id, role, created_at) VALUES
  ('u_owner',  'main', 'owner',  NOW()::text),
  ('u_member', 'main', 'member', NOW()::text)
ON CONFLICT (user_id, agent_id) DO UPDATE SET role = EXCLUDED.role;

INSERT INTO user_identities (user_id, channel, channel_user_id, created_at) VALUES
  ('u_member', 'slack', 'U02BOB', NOW()::text)
ON CONFLICT (channel, channel_user_id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
