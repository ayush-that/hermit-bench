---
id: 05_Memory_Introspection_task_5_fts_recall
name: Recall a memory by full-text search query
category: 05_Memory_Introspection
timeout_seconds: 240
---

## Prompt

How do I rotate the Stripe webhook secret? Check your long-term memory using `memory_recall` — there should be a runbook entry. Quote the relevant text from the memory in your final reply.

## Expected Behavior

The agent calls `memory_recall` with a query like `Stripe webhook secret` (or `rotate Stripe`) that hits the seeded memory whose content describes the Stripe webhook secret rotation runbook. The reply cites the runbook content.

## Grading Criteria

- [ ] `memory_recall` was invoked with a query mentioning `stripe` (case-insensitive).
- [ ] The assistant response mentions either `stripe` AND `webhook`, or `runbook`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess, json as _json
    scores = {
        "recall_invoked_with_stripe": 0.0,
        "response_cites_runbook": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    # 1) Did the agent call memory_recall with a query mentioning "stripe"?
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT payload::text FROM session_events "
             "WHERE agent_id='main' AND event_type='tool_call' "
             "AND payload->>'name' = 'memory_recall';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        r = None
    if r and r.returncode == 0:
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = _json.loads(line)
            except Exception:
                continue
            args = payload.get("args") or {}
            q = (args.get("query") or "").lower() if isinstance(args, dict) else ""
            if "stripe" in q:
                scores["recall_invoked_with_stripe"] = 1.0
                break

    # 2) Does any assistant message cite the runbook (or mention stripe + webhook)?
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT string_agg(content, ' || ') FROM session_events "
             "WHERE agent_id='main' AND event_type='assistant' "
             "AND content IS NOT NULL;"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        r = None
    if r and r.returncode == 0:
        content = (r.stdout or "").lower()
        if ("stripe" in content and "webhook" in content) or "runbook" in content:
            scores["response_cites_runbook"] = 1.0

    scores["overall_score"] = (
        scores["recall_invoked_with_stripe"]
        + scores["response_cites_runbook"]
    ) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_5_fts_recall
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
# 20 memories: 1 about Stripe webhook rotation, 19 unrelated distractors.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'runbook-stripe-webhook', 'Stripe webhook secret rotation runbook: open the Stripe dashboard, regenerate the signing secret, then update STRIPE_WEBHOOK_SECRET in vault and redeploy the webhook handler.', NOW()::text, NOW()::text),
  ('main', 'fact-favorite-color',   'Alice''s favorite color is amethyst purple.', NOW()::text, NOW()::text),
  ('main', 'pref-units',            'Alice prefers metric units in all answers.', NOW()::text, NOW()::text),
  ('main', 'pref-format',           'Alice prefers markdown tables for structured data.', NOW()::text, NOW()::text),
  ('main', 'fact-city',             'Alice lives in Berlin.', NOW()::text, NOW()::text),
  ('main', 'fact-timezone',         'Alice is in the Europe/Berlin timezone.', NOW()::text, NOW()::text),
  ('main', 'project-acme',          'Acme migration project is paused until 2026-07.', NOW()::text, NOW()::text),
  ('main', 'project-onboarding',    'New hire onboarding doc lives in Notion under Engineering / Onboarding.', NOW()::text, NOW()::text),
  ('main', 'fact-laptop',           'Alice''s personal laptop is a MacBook Air M2.', NOW()::text, NOW()::text),
  ('main', 'fact-keyboard',         'Alice uses a Kinesis Advantage keyboard.', NOW()::text, NOW()::text),
  ('main', 'pref-music',            'Alice listens to ambient electronic music while coding.', NOW()::text, NOW()::text),
  ('main', 'fact-dog',              'Alice has a corgi named Pixel.', NOW()::text, NOW()::text),
  ('main', 'project-launch',        'Amiko launch is scheduled for 2026-06-01.', NOW()::text, NOW()::text),
  ('main', 'fact-allergy',          'Alice is allergic to penicillin.', NOW()::text, NOW()::text),
  ('main', 'pref-meeting',          'Alice prefers 30-minute meetings, no longer.', NOW()::text, NOW()::text),
  ('main', 'fact-email',            'Alice''s work email is alice@example.com.', NOW()::text, NOW()::text),
  ('main', 'fact-github',           'Alice''s GitHub handle is alicedoe.', NOW()::text, NOW()::text),
  ('main', 'pref-tone',             'Keep emails written on Alice''s behalf under 80 words.', NOW()::text, NOW()::text),
  ('main', 'fact-bike',             'Alice rides a Brompton folding bike to the office.', NOW()::text, NOW()::text),
  ('main', 'fact-coffee',           'Alice prefers oat-milk flat whites, no sugar.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
