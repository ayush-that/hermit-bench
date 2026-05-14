---
id: 05_Memory_Introspection_task_1_recall_existing
name: Recall an existing long-term memory
category: 05_Memory_Introspection
timeout_seconds: 180
---

## Prompt

What's my favorite coffee?

## Expected Behavior

The agent recalls the seeded long-term memory `fact-favorite-coffee` (via the `memory_recall` tool) and answers with `oat-milk` (or `oat milk`).

## Grading Criteria

- [ ] The assistant response mentions `oat-milk` or `oat milk`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    scores = {"recalled_oat_milk": 0.0, "overall_score": 0.0}

    if not transcript:
        return scores

    for msg in transcript:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role") or msg.get("event_type")
        if role != "assistant":
            continue
        content = (msg.get("content") or "").lower()
        if "oat-milk" in content or "oat milk" in content or "oatmilk" in content:
            scores["recalled_oat_milk"] = 1.0
            break

    scores["overall_score"] = scores["recalled_oat_milk"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_1_recall_existing
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
# Memory seeds must run AFTER the gateway boots — the `memories` table is
# created by the drizzle migrations at gateway startup, not before.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'fact-favorite-coffee', 'Alice prefers oat-milk flat whites, no sugar.', NOW()::text, NOW()::text),
  ('main', 'fact-workout-time',    'Alice works out Tuesday and Thursday mornings at 6:30 AM.', NOW()::text, NOW()::text),
  ('main', 'fact-allergy',         'Alice is allergic to penicillin. This is critical.', NOW()::text, NOW()::text),
  ('main', 'pref-tone',            'When writing emails on Alice''s behalf, keep them under 80 words.', NOW()::text, NOW()::text),
  ('main', 'project-amiko-launch', 'Amiko launch is scheduled for 2026-06-01.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
