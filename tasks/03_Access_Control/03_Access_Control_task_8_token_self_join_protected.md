---
id: 03_Access_Control_task_8_token_self_join_protected
name: identity_link_request issues a join token
category: 03_Access_Control
timeout_seconds: 240
---

## Prompt

I'd like to link this current chat session with my account on another channel. Please call the `identity_link_request` tool to generate a short-lived join token I can redeem on the other side.

Reply with the token and the expiry. Do not call any other identity tool.

## Expected Behavior

The session caller is an existing user `u_joiner` with an explicit `cli`
identity (root@cli) so the protected-agent runtime allows the message
through. `identity_link_request` is a `defaultGrants: [{type:'any'}]`
tool, so the agent can call it regardless of role.

**Simulation note.** The actual redeem step (`identity_link_confirm`) is
hard to drive end-to-end inside the bench because: (1) link tokens live in
process memory in `apps/agent/src/identity-link-tokens.ts` — we can't
preseed them via SQL, (2) `identity_link_confirm` must be invoked from a
different channel than the one that issued the token, and the bench
runner only drives a single CLI session. We therefore assert the
*request* half of the flow: the join-token tool was callable on a
`protected` agent, the joiner user/identity rows exist, and a
`tool_result` for `identity_link_request` was recorded with no error.

## Grading Criteria

- [ ] `users` table has row `user_id='u_joiner'`.
- [ ] `user_identities` has `(channel='cli', channel_user_id='root', user_id='u_joiner')`.
- [ ] At least one `session_events` row with `event_type='tool_result'`,
      `payload->>'tool'='identity_link_request'`, and
      `payload->>'isError' IS DISTINCT FROM 'true'`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {
        "joiner_user_row": 0.0,
        "joiner_identity_row": 0.0,
        "link_request_invoked": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def psql(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    if psql("SELECT count(*) FROM users WHERE user_id='u_joiner';") == "1":
        scores["joiner_user_row"] = 1.0

    if psql(
        "SELECT count(*) FROM user_identities "
        "WHERE user_id='u_joiner' AND channel='cli' AND channel_user_id='root';"
    ) == "1":
        scores["joiner_identity_row"] = 1.0

    invoked = psql(
        "SELECT count(*) FROM session_events "
        "WHERE agent_id='main' AND event_type='tool_result' "
        "AND payload->>'name'='identity_link_request' "
        "AND (payload->>'isError') IS DISTINCT FROM 'true';"
    )
    try:
        if int(invoked) >= 1:
            scores["link_request_invoked"] = 1.0
    except ValueError:
        pass

    scores["overall_score"] = (
        scores["joiner_user_row"]
        + scores["joiner_identity_row"]
        + scores["link_request_invoked"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/03_Access_Control/task_8_token_self_join_protected
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

# Flip the agent to access='protected' so the runtime would normally
# drop messages from unknown identities — we pre-seed the joiner so the
# message lands, then ask the agent to mint a join token.
hermit config --agent main set security.access protected || true

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_owner',  'Owner',  NOW()::text, NOW()::text),
  ('u_joiner', 'Joiner', NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_agents (user_id, agent_id, role, created_at) VALUES
  ('u_owner',  'main', 'owner', NOW()::text),
  ('u_joiner', 'main', 'guest', NOW()::text)
ON CONFLICT (user_id, agent_id) DO UPDATE SET role = EXCLUDED.role;

INSERT INTO user_identities (user_id, channel, channel_user_id, created_at) VALUES
  ('u_joiner', 'cli', 'root', NOW()::text)
ON CONFLICT (channel, channel_user_id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
