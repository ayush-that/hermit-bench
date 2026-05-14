---
id: 04_Channel_Routing_task_6_telegram_webhook_register
name: Switch telegram channel from polling to webhook mode
category: 04_Channel_Routing
timeout_seconds: 180
---

## Prompt

You are agent `main` and the owner just asked:

> Switch the telegram channel from polling to webhook mode.

The agent's telegram channel is stored as a row in the `agent_channels` table (`agent_id='main'`, `channel_type='telegram'`). The mode lives under `config->>'mode'`; today it equals `polling`.

Update that row's `config` JSON so `config->>'mode' = 'webhook'`. All other keys in `config` must be preserved.

You have shell access. Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`. Hint:

```
UPDATE agent_channels
SET config = jsonb_set(config, '{mode}', '"webhook"'::jsonb),
    updated_at = NOW()::text
WHERE agent_id='main' AND channel_type='telegram';
```

When the update is committed, reply with `DONE`.

## Expected Behavior

Channel adapters are not running in the test container. The `agent_channels` telegram row is seeded with `config = {"mode":"polling","allowed_chat_ids":[55501]}`. The agent should flip `config->>'mode'` to `webhook` while preserving the `allowed_chat_ids` key.

## Grading Criteria

- [ ] `agent_channels` telegram row has `config->>'mode' = 'webhook'`.
- [ ] `config->'allowed_chat_ids'` is still present (other keys preserved).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"mode_webhook": 0.0, "other_keys_preserved": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "|", "-c",
             "SELECT COALESCE(config->>'mode',''), "
             "COALESCE((config->'allowed_chat_ids')::text,'') "
             "FROM agent_channels "
             "WHERE agent_id='main' AND channel_type='telegram' LIMIT 1;"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0 or not r.stdout.strip():
        return scores

    parts = r.stdout.strip().split("|", 1)
    mode = parts[0] if parts else ""
    allowed = parts[1] if len(parts) > 1 else ""

    if mode == "webhook":
        scores["mode_webhook"] = 1.0
    if "55501" in allowed:
        scores["other_keys_preserved"] = 1.0

    scores["overall_score"] = (scores["mode_webhook"] + scores["other_keys_preserved"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_6_telegram_webhook_register
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
-- Seed a telegram channel row in polling mode. token_ciphertext / token_prefix
-- are required NOT NULL columns; we use placeholder values since no live
-- bridge will ever decrypt them in the test container.
INSERT INTO agent_channels (
  id, agent_id, kind, channel_type, namespace, label, enabled,
  config, token_prefix, token_ciphertext,
  created_at, updated_at
) VALUES (
  'ch_telegram_main', 'main', 'builtin', 'telegram', 'telegram', 'telegram', true,
  '{"mode":"polling","allowed_chat_ids":[55501]}'::jsonb,
  'fake-prefix-',
  'fake-ciphertext',
  NOW()::text, NOW()::text
)
ON CONFLICT (id) DO UPDATE SET
  config = EXCLUDED.config,
  enabled = EXCLUDED.enabled,
  updated_at = EXCLUDED.updated_at;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
