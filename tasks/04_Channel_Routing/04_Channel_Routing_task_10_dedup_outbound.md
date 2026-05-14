---
id: 04_Channel_Routing_task_10_dedup_outbound
name: Send pong to slack:ops twice with sensible dedup handling
category: 04_Channel_Routing
timeout_seconds: 240
---

## Prompt

You are agent `main`. The owner asks:

> Send `pong` to slack channel `slack:ops` twice.

Channel adapters are not running in this test container. Use the `mock_outbound` table to simulate the Slack adapter delivery. Schema:

```
agent_id      text       -- 'main'
channel       text       -- 'slack'
to_channel_id text       -- 'slack:ops'
body          text       -- the message text
created_at    text
```

You have two acceptable strategies:

1. Send the message twice — but the second body must NOT be a byte-for-byte duplicate of the first (e.g. append `(second)` or a counter), to avoid pure spam.
2. Send the message once and explain in your reply that you de-duplicated the second send for safety.

Either strategy is accepted. When you are done, reply with `DONE` if you sent twice (strategy 1) OR an explanation sentence if you only sent once (strategy 2).

Postgres at `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`.

## Expected Behavior

The agent records outbound messages in `mock_outbound`. Per the dedup rule, two rows must NOT be byte-identical. Either:

- two rows exist with different `body` values (e.g. `pong` and `pong (second)`), or
- one row exists with `body='pong'` AND the assistant final reply mentions de-duplication / idempotency / "only sent once".

## Grading Criteria

- [ ] At least one `mock_outbound` row with `to_channel_id='slack:ops'` and body matching `pong%`.
- [ ] Either (a) two rows with distinct bodies, or (b) one row plus an assistant reply that explains the dedup choice.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"outbound_present": 0.0, "dedup_strategy": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    bodies_raw = q(
        "SELECT body FROM mock_outbound "
        "WHERE agent_id='main' AND channel='slack' "
        "AND to_channel_id='slack:ops' "
        "AND lower(body) LIKE 'pong%';"
    )
    bodies = [b for b in bodies_raw.splitlines() if b]

    if bodies:
        scores["outbound_present"] = 1.0

    final_text = ""
    if transcript:
        for evt in reversed(transcript):
            if isinstance(evt, dict) and (
                evt.get("event_type") == "assistant_message"
                or evt.get("role") == "assistant"
            ):
                c = evt.get("content") or ""
                if isinstance(c, str) and c.strip():
                    final_text = c.strip().lower()
                    break

    distinct_bodies = len(set(bodies))
    explained = any(
        kw in final_text
        for kw in ("dedup", "duplicate", "idempot", "only sent once", "skipped the second", "didn't send")
    )

    if distinct_bodies >= 2:
        scores["dedup_strategy"] = 1.0
    elif len(bodies) == 1 and explained:
        scores["dedup_strategy"] = 1.0
    elif len(bodies) >= 1 and explained:
        scores["dedup_strategy"] = 0.5

    scores["overall_score"] = (scores["outbound_present"] + scores["dedup_strategy"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_10_dedup_outbound
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE IF NOT EXISTS mock_outbound (
  id            serial PRIMARY KEY,
  agent_id      text NOT NULL,
  channel       text NOT NULL,
  to_channel_id text NOT NULL,
  body          text NOT NULL,
  created_at    text NOT NULL DEFAULT NOW()::text
);
SQL
```

## Env

```
OPENROUTER_API_KEY
```
