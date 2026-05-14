---
id: 04_Channel_Routing_task_7_disable_channel_temp
name: Disable the slack channel for a temporary mute
category: 04_Channel_Routing
timeout_seconds: 180
---

## Prompt

You are agent `main` and the owner just asked:

> I'm muting Slack for 1 hour. Disable the slack channel.

The slack channel for agent `main` is a row in the `agent_channels` table (`channel_type='slack'`). Set its `enabled` flag to `false`.

You have shell access. Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`. Hint:

```
UPDATE agent_channels
SET enabled = false, updated_at = NOW()::text
WHERE agent_id='main' AND channel_type='slack';
```

When the update is committed, reply with `DONE`.

## Expected Behavior

Channel adapters are not running in the test container. The slack `agent_channels` row is seeded with `enabled=true`; the agent should flip it to `false`. Other channel rows (telegram, discord) must remain untouched.

## Grading Criteria

- [ ] `agent_channels.enabled = false` for the slack row.
- [ ] `agent_channels.enabled = true` for the telegram row (untouched).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"slack_disabled": 0.0, "telegram_untouched": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    slack = q(
        "SELECT enabled FROM agent_channels "
        "WHERE agent_id='main' AND channel_type='slack' LIMIT 1;"
    )
    if slack.lower() in ("f", "false"):
        scores["slack_disabled"] = 1.0

    telegram = q(
        "SELECT enabled FROM agent_channels "
        "WHERE agent_id='main' AND channel_type='telegram' LIMIT 1;"
    )
    if telegram.lower() in ("t", "true"):
        scores["telegram_untouched"] = 1.0

    scores["overall_score"] = (scores["slack_disabled"] + scores["telegram_untouched"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_7_disable_channel_temp
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
-- Three builtin channel rows, all enabled at seed time.
INSERT INTO agent_channels (
  id, agent_id, kind, channel_type, namespace, label, enabled,
  config, token_prefix, token_ciphertext, created_at, updated_at
) VALUES
  ('ch_telegram_main', 'main', 'builtin', 'telegram', 'telegram', 'telegram', true,
   '{"mode":"polling"}'::jsonb, 'fake-tg-pre', 'fake-tg-cipher',
   NOW()::text, NOW()::text),
  ('ch_slack_main',    'main', 'builtin', 'slack',    'slack',    'slack',    true,
   '{}'::jsonb,                 'fake-sl-pre', 'fake-sl-cipher',
   NOW()::text, NOW()::text),
  ('ch_discord_main',  'main', 'builtin', 'discord',  'discord',  'discord',  true,
   '{}'::jsonb,                 'fake-dc-pre', 'fake-dc-cipher',
   NOW()::text, NOW()::text)
ON CONFLICT (id) DO UPDATE SET
  enabled = EXCLUDED.enabled,
  updated_at = EXCLUDED.updated_at;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
