---
id: 01_CLI_Fluency_task_1_create_agent
name: Create and enable a new agent
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

Create a new OpenHermit agent named `notes` and make sure it is enabled (accepting requests).

You have shell access. Use the `hermit` CLI. The relevant commands are:

- `hermit agents create <agentId>` to register the agent.
- `hermit agents enable <agentId>` to flip its status to `active`.

When you are done, reply with `DONE` and nothing else.

## Expected Behavior

After the agent finishes, the `agents` table contains a row with `agent_id='notes'` and `status='active'`.

## Grading Criteria

- [ ] `notes` row exists in the `agents` table.
- [ ] Its `status` column equals `active`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"agent_exists": 0.0, "agent_active": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c", "SELECT status FROM agents WHERE agent_id='notes';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0:
        return scores

    status = r.stdout.strip()
    if status:
        scores["agent_exists"] = 1.0
    if status == "active":
        scores["agent_active"] = 1.0

    scores["overall_score"] = (scores["agent_exists"] + scores["agent_active"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_1_create_agent
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
```

## Env

```
OPENROUTER_API_KEY
```
