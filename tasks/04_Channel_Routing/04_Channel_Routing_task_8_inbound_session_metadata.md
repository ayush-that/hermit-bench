---
id: 04_Channel_Routing_task_8_inbound_session_metadata
name: Materialize an inbound telegram session with correct metadata
category: 04_Channel_Routing
timeout_seconds: 180
---

## Prompt

You are agent `main`. A new inbound Telegram message just arrived:

- chat id: `12345`
- sender: `u_member`
- text: `hello there`

In production, the Telegram bridge would call `openSession` for a new session id formatted `telegram:YYYY-MM-DD-<8hex>` with metadata `{"telegram_chat_id":"12345"}` and then post the inbound message.

The bridge is NOT running in this test container. Your job is to manually materialize the same database state by inserting one row into `sessions`:

- `agent_id = 'main'`
- `session_id` starts with `telegram:` (any suffix is fine; the bridge uses `telegram:YYYY-MM-DD-<8hex>`)
- `source_kind = 'channel'`
- `source_platform = 'telegram'`
- `metadata` is JSONB with `telegram_chat_id = '12345'`
- the row passes `metadata->>'telegram_chat_id' = '12345'`

Other required columns (NOT NULL): `interactive`, `created_at`, `last_activity_at`, `status`, `type`, `user_ids`. Use reasonable defaults (e.g. `interactive=1`, status `running`, type `direct`, user_ids `["u_member"]`).

Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`.

When the row is inserted, reply with `DONE`.

## Expected Behavior

The agent inserts exactly one new `sessions` row whose `session_id LIKE 'telegram:%'` and whose `metadata->>'telegram_chat_id' = '12345'`.

## Grading Criteria

- [ ] One sessions row exists with `agent_id='main'`, `session_id LIKE 'telegram:%'`, `metadata->>'telegram_chat_id' = '12345'`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"session_row_present": 0.0, "metadata_correct": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    prefix_cnt = q(
        "SELECT count(*) FROM sessions "
        "WHERE agent_id='main' AND session_id LIKE 'telegram:%';"
    )
    if prefix_cnt and prefix_cnt != "0":
        scores["session_row_present"] = 1.0

    meta_cnt = q(
        "SELECT count(*) FROM sessions "
        "WHERE agent_id='main' AND session_id LIKE 'telegram:%' "
        "AND metadata->>'telegram_chat_id' = '12345';"
    )
    if meta_cnt and meta_cnt != "0":
        scores["metadata_correct"] = 1.0

    scores["overall_score"] = (scores["session_row_present"] + scores["metadata_correct"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_8_inbound_session_metadata
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_member', 'Member', NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
