---
id: 01_CLI_Fluency_task_7_mcp_enable
name: Enable an MCP server for one agent only
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

Enable the MCP server `mcp_github` for agent `notes` **only**. Do not enable it on any other agent and do not write a wildcard assignment.

You have shell access. The relevant command is:

```
hermit mcp enable mcp_github --agent notes
```

When the assignment has been created, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `agent_mcp_servers` table has exactly one row with `mcp_server_id='mcp_github'` and `agent_id='notes'` and `enabled=true`. There is no wildcard (`agent_id='*'`) row for that MCP server.

## Grading Criteria

- [ ] Exactly one enabled assignment row for `mcp_github`, on agent `notes`.
- [ ] No `*` wildcard row for `mcp_github`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"notes_enabled": 0.0, "no_wildcard": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    notes_row = q(
        "SELECT count(*) FROM agent_mcp_servers "
        "WHERE agent_id='notes' AND mcp_server_id='mcp_github' AND enabled=true;"
    )
    wildcard_row = q(
        "SELECT count(*) FROM agent_mcp_servers "
        "WHERE agent_id='*' AND mcp_server_id='mcp_github';"
    )

    if notes_row == "1":
        scores["notes_enabled"] = 1.0
    if wildcard_row == "0":
        scores["no_wildcard"] = 1.0

    scores["overall_score"] = (scores["notes_enabled"] + scores["no_wildcard"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_7_mcp_enable
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
hb_seed_agent notes

# Register the mcp_github server in the registry. No assignment yet — the
# agent has to create it.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO mcp_servers (id, name, description, url, headers, metadata, created_at, updated_at)
VALUES ('mcp_github', 'GitHub MCP', 'GitHub MCP server', 'https://example.invalid/mcp', '{}', '{}', NOW()::text, NOW()::text)
ON CONFLICT (id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
