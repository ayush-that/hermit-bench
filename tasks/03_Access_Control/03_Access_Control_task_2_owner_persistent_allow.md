---
id: 03_Access_Control_task_2_owner_persistent_allow
name: Owner approves an exec request persistently
category: 03_Access_Control
timeout_seconds: 240
---

## Prompt

There is a pending approval request from user `u_member` for the `exec` tool.

The request id is `req_member_exec_001`. Approve it, and make the approval **persistent** (so future identical requests from this user are allowed automatically without re-prompting).

Use the `approval_review` owner tool. Set `decision='approved'` and `resolution='persistent'`.

When done, reply with `DONE`.

## Expected Behavior

The agent runs as the owner (`u_owner`). It calls `approval_review(id='req_member_exec_001', decision='approved', resolution='persistent')`. The runtime resolves the request and **auto-creates an allow policy row** in `agent_policies` granting `u_member` access to the `exec` tool.

## Grading Criteria

- [ ] `approval_requests.status = 'approved'` and `resolution = 'persistent'` for `req_member_exec_001`.
- [ ] At least one row in `agent_policies` with `resource_type='tool'`, `resource_key='exec'`, `effect='allow'`, and `grants @> '[{"type":"user","value":"u_member"}]'`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"approval_resolved": 0.0, "allow_policy_row": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def psql(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    resolved = psql(
        "SELECT count(*) FROM approval_requests "
        "WHERE id='req_member_exec_001' "
        "AND status='approved' AND resolution='persistent';"
    )
    if resolved == "1":
        scores["approval_resolved"] = 1.0

    allow_row = psql(
        "SELECT count(*) FROM agent_policies "
        "WHERE agent_id='main' AND resource_type='tool' "
        "AND resource_key='exec' AND effect='allow' "
        "AND grants @> '[{\"type\":\"user\",\"value\":\"u_member\"}]'::jsonb;"
    )
    if allow_row not in ("", "0"):
        scores["allow_policy_row"] = 1.0

    scores["overall_score"] = (
        scores["approval_resolved"] + scores["allow_policy_row"]
    ) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/03_Access_Control/task_2_owner_persistent_allow
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
-- Owner + member rows. root@cli → u_owner so the agent has the
-- `approval_review` tool available (owner-only).
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_owner',  'Owner',  NOW()::text, NOW()::text),
  ('u_member', 'Member', NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_agents (user_id, agent_id, role, created_at) VALUES
  ('u_owner',  'main', 'owner', NOW()::text),
  ('u_member', 'main', 'user',  NOW()::text)
ON CONFLICT (user_id, agent_id) DO UPDATE SET role = EXCLUDED.role;

INSERT INTO user_identities (user_id, channel, channel_user_id, created_at) VALUES
  ('u_owner', 'cli', 'root', NOW()::text)
ON CONFLICT (channel, channel_user_id) DO NOTHING;

-- Seed the pending approval request the owner is about to resolve.
INSERT INTO approval_requests
  (id, agent_id, session_id, requester_id, resource_type, resource_key,
   scope, status, created_at, ttl_minutes)
VALUES
  ('req_member_exec_001', 'main', 'unknown', 'u_member',
   'tool', 'exec', '{}'::jsonb, 'pending', NOW()::text, 60)
ON CONFLICT (id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
