---
id: 04_Channel_Routing_task_3_group_mention_reply
name: Reply in a group when explicitly mentioned
category: 04_Channel_Routing
timeout_seconds: 180
---

## Prompt

You are agent `main`. The following situation just happened on Telegram:

- channel: a Telegram group
- the message sender `u_member` is NOT the owner
- the agent `main` WAS mentioned in the message
- the message text is: `@main can you compute 17 * 23?`

Under OpenHermit's group-routing rules, a non-owner mention triggers a reply. Answer the user's question. Your reply must contain the numeric answer to `17 * 23`.

## Expected Behavior

Channel adapters are not running in the test container — the group situation is simulated via the prompt. The agent should recognize this as a mention-triggered turn and reply with the product (`391`).

## Grading Criteria

- [ ] The assistant's final reply contains the substring `391`.
- [ ] The reply is NOT exactly `<NO_REPLY>`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    scores = {"contains_answer": 0.0, "not_no_reply": 0.0, "overall_score": 0.0}

    if not transcript:
        return scores

    final_text = ""
    for evt in reversed(transcript):
        if not isinstance(evt, dict):
            continue
        if evt.get("event_type") == "assistant_message" or evt.get("role") == "assistant":
            content = evt.get("content") or ""
            if isinstance(content, str) and content.strip():
                final_text = content.strip()
                break

    if "391" in final_text:
        scores["contains_answer"] = 1.0
    if final_text and final_text != "<NO_REPLY>":
        scores["not_no_reply"] = 1.0

    scores["overall_score"] = (scores["contains_answer"] + scores["not_no_reply"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_3_group_mention_reply
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_owner',  'Owner',  NOW()::text, NOW()::text),
  ('u_member', 'Member', NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_agents (user_id, agent_id, role, created_at) VALUES
  ('u_owner',  'main', 'owner',  NOW()::text),
  ('u_member', 'main', 'member', NOW()::text)
ON CONFLICT (user_id, agent_id) DO UPDATE SET role = EXCLUDED.role;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
