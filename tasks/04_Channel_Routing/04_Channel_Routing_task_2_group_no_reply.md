---
id: 04_Channel_Routing_task_2_group_no_reply
name: Stay silent in a group chat when not mentioned
category: 04_Channel_Routing
timeout_seconds: 180
---

## Prompt

You are agent `main`. The following situation just happened on Telegram:

- channel: a Telegram group
- the group's owner is `u_owner`
- the message sender is `u_member` (NOT the owner)
- the agent (`main`) was NOT mentioned in the message
- the message text is: `Anyone want lunch?`

OpenHermit's group-routing rules say:

- owners always trigger a reply
- non-owner mentioned messages trigger a reply
- non-owner unmentioned messages MUST NOT trigger a reply — the adapter expects the agent to respond with the literal token `<NO_REPLY>` so the outbound is suppressed.

Reply with exactly `<NO_REPLY>` (no quotes, no other text, no whitespace before or after) and nothing else.

## Expected Behavior

Channel adapters are not live in the test container — we simulate the group situation via the prompt. The agent should output exactly `<NO_REPLY>` because the sender is not the owner and the agent is not mentioned. The grader inspects the assistant's final transcript reply.

## Grading Criteria

- [ ] The assistant's final reply is exactly `<NO_REPLY>` (after trimming whitespace).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    scores = {"no_reply_emitted": 0.0, "overall_score": 0.0}

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

    if final_text == "<NO_REPLY>":
        scores["no_reply_emitted"] = 1.0

    scores["overall_score"] = scores["no_reply_emitted"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/04_Channel_Routing/task_2_group_no_reply
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

# Seed user identities so the owner/member distinction is grounded in the DB,
# even though the grader only inspects the assistant reply.
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
