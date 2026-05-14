---
id: 02_Tool_Composition_task_7_user_list_to_md
name: List users and render them as a markdown table
category: 02_Tool_Composition
timeout_seconds: 240
---

## Prompt

Call the `user_list` tool to get all users on this agent. Then write a markdown table to `/tmp_workspace/results/users.md` with exactly four columns, in this order:

```
| user_id | name | role | channels |
```

- `user_id` is the user's `userId` (e.g. `u_alice`).
- `name` is the user's `name` field.
- `role` is the user's role on this agent (e.g. `owner`, `user`, `guest`).
- `channels` is a comma-separated list of `channel:channel_user_id` pairs (e.g. `telegram:tg_alice`).

The table must include a markdown header row and a `|---|---|---|---|` separator row. Sort the rows alphabetically by `user_id`.

When the file has been written, reply with `DONE`.

(Note: the original spec referenced a `display_name` column, but the verified OpenHermit schema stores the human-readable label under `users.name`. The substitution is intentional and the grader uses the real column.)

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/users.md` exists and contains one row per seeded user (`u_alice`, `u_bob`, `u_carol`), with the correct name, role, and at least one channel identity per user.

## Grading Criteria

- [ ] File exists at `/tmp_workspace/results/users.md`.
- [ ] All three seeded user ids appear as the first cell of some row.
- [ ] Each row's row text contains the correct `name`, `role`, and at least one `channel:channel_user_id` pair from the DB.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {
        "file_exists": 0.0,
        "ids_present": 0.0,
        "fields_match": 0.0,
        "overall_score": 0.0,
    }
    path = os.path.join(workspace_path, "results", "users.md")
    if not os.path.isfile(path):
        return scores
    scores["file_exists"] = 1.0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
    except OSError:
        return scores

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql):
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "\t", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip().splitlines() if r.returncode == 0 else []

    expected_ids = {"u_alice", "u_bob", "u_carol"}
    found_ids = {uid for uid in expected_ids if uid in body}
    scores["ids_present"] = len(found_ids) / len(expected_ids)

    truth: dict[str, dict] = {}
    for line in q(
        "SELECT u.user_id, u.name, ua.role "
        "FROM users u "
        "LEFT JOIN user_agents ua ON ua.user_id = u.user_id AND ua.agent_id = 'main' "
        "WHERE u.user_id IN ('u_alice','u_bob','u_carol');"
    ):
        parts = line.split("\t")
        if len(parts) >= 3:
            uid, name, role = parts[0], parts[1], parts[2]
            truth[uid] = {"name": name, "role": role, "channels": []}
    for line in q(
        "SELECT user_id, channel, channel_user_id FROM user_identities "
        "WHERE user_id IN ('u_alice','u_bob','u_carol');"
    ):
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0] in truth:
            truth[parts[0]]["channels"].append(f"{parts[1]}:{parts[2]}")

    if not truth:
        scores["overall_score"] = scores["file_exists"] / 3.0 + scores["ids_present"] / 3.0
        return scores

    field_hits = 0
    field_max = 0
    for uid, info in truth.items():
        # Each user contributes 3 sub-checks: name, role, at least one channel id.
        field_max += 3
        # Find a line that contains the uid and check the other fields are on that line.
        line_match = ""
        for line in body.splitlines():
            if uid in line:
                line_match = line
                break
        if not line_match:
            continue
        if info["name"] and info["name"] in line_match:
            field_hits += 1
        if info["role"] and info["role"] in line_match:
            field_hits += 1
        if any(ch in line_match for ch in info["channels"]):
            field_hits += 1

    scores["fields_match"] = field_hits / field_max if field_max else 0.0
    scores["overall_score"] = (
        scores["file_exists"]
        + scores["ids_present"]
        + scores["fields_match"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_7_user_list_to_md
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

# Seed three users with deterministic ids, names, agent roles, and channels.
# The grader queries Postgres for ground truth (users + user_agents +
# user_identities) and reconstructs the expected markdown table from that.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO users (user_id, name, created_at, updated_at) VALUES
  ('u_alice',  'Alice',  NOW()::text, NOW()::text),
  ('u_bob',    'Bob',    NOW()::text, NOW()::text),
  ('u_carol',  'Carol',  NOW()::text, NOW()::text)
ON CONFLICT (user_id) DO UPDATE SET name = EXCLUDED.name, updated_at = EXCLUDED.updated_at;

INSERT INTO user_agents (user_id, agent_id, role, created_at) VALUES
  ('u_alice', 'main', 'owner', NOW()::text),
  ('u_bob',   'main', 'user',  NOW()::text),
  ('u_carol', 'main', 'guest', NOW()::text)
ON CONFLICT (user_id, agent_id) DO UPDATE SET role = EXCLUDED.role;

INSERT INTO user_identities (channel, channel_user_id, user_id, created_at) VALUES
  ('telegram', 'tg_alice',  'u_alice', NOW()::text),
  ('discord',  'dc_bob',    'u_bob',   NOW()::text),
  ('cli',      'cli_carol', 'u_carol', NOW()::text)
ON CONFLICT (channel, channel_user_id) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
