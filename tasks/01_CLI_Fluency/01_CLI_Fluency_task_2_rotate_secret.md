---
id: 01_CLI_Fluency_task_2_rotate_secret
name: Rotate an agent secret
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

The third-party API token stored under the secret name `STRIPE_API_KEY` on agent `main` has been rotated. The new value is sitting in `/tmp_workspace/new_key.txt`. Replace the `STRIPE_API_KEY` secret on agent `main` with that new value.

You have shell access. The relevant command is:

```
hermit config --agent main secrets set STRIPE_API_KEY "<the new value>"
```

When the secret has been updated, reply with `DONE` and nothing else.

## Expected Behavior

After the agent finishes, the `agent_secrets` row for `(main, STRIPE_API_KEY)` has an `updated_at` strictly newer than its `created_at`.

## Grading Criteria

- [ ] The secret row's `updated_at` is later than its `created_at`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"secret_rotated": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "|",
             "-c",
             "SELECT created_at, updated_at FROM agent_secrets "
             "WHERE agent_id='main' AND name='STRIPE_API_KEY';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0 or not r.stdout.strip():
        return scores

    parts = r.stdout.strip().split("|", 1)
    if len(parts) != 2:
        return scores

    created_at, updated_at = parts[0].strip(), parts[1].strip()
    if updated_at and created_at and updated_at > created_at:
        scores["secret_rotated"] = 1.0

    scores["overall_score"] = scores["secret_rotated"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_2_rotate_secret
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
# Seed an initial value so the row's created_at is set; the agent must rotate it.
hb_seed_secret main STRIPE_API_KEY "sk-oldkey-deadbeef"
# Make sure created_at != updated_at semantics work: sleep to avoid same-second timestamps.
sleep 2
# Drop the rotation target into the workspace.
echo "sk-newkey-cafef00d" > /tmp_workspace/new_key.txt
```

## Env

```
OPENROUTER_API_KEY
```
