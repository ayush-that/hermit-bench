---
id: 01_CLI_Fluency_task_10_status_json
name: Aggregate fleet status into JSON
category: 01_CLI_Fluency
timeout_seconds: 240
---

## Prompt

Produce a JSON file at `/tmp_workspace/results/fleet.json` that lists every agent in the fleet. The output must be a JSON array of objects, one per agent, each shaped like:

```
{ "id": "<agent_id>", "status": "<active|disabled>", "active_sessions": <int> }
```

- `id` and `status` come from `hermit agents list` (or the `agents` table).
- `active_sessions` is the count of rows in the `sessions` table for that agent whose `status` column equals `running`.

The Postgres database is on `127.0.0.1:5432`, db `hermit`, user `hermit`, password `hermit`. You may use `psql` directly if it is easier than calling `hermit`.

When the file has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/fleet.json` parses as a JSON array. For each of the three seeded agents (`main`, `notes`, `assistant`), the array contains an object with the matching `id`, `status`, and `active_sessions` count.

## Grading Criteria

- [ ] File parses as JSON array.
- [ ] All three agents present with correct `status`.
- [ ] Each agent's `active_sessions` matches the running-session count in the DB.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import json, os, subprocess
    scores = {
        "valid_json": 0.0,
        "agents_present": 0.0,
        "session_counts_match": 0.0,
        "overall_score": 0.0,
    }

    path = os.path.join(workspace_path, "results", "fleet.json")
    if not os.path.isfile(path):
        return scores
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return scores
    if not isinstance(data, list):
        return scores
    scores["valid_json"] = 1.0

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    def q(sql: str) -> str:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "|", "-c", sql],
            capture_output=True, text=True, env=env, timeout=15,
        )
        return r.stdout.strip() if r.returncode == 0 else ""

    truth_status: dict[str, str] = {}
    for line in q("SELECT agent_id, status FROM agents;").splitlines():
        if "|" in line:
            aid, st = line.split("|", 1)
            truth_status[aid] = st

    truth_sessions: dict[str, int] = {}
    for line in q(
        "SELECT agent_id, count(*) FROM sessions "
        "WHERE status='running' GROUP BY agent_id;"
    ).splitlines():
        if "|" in line:
            aid, cnt = line.split("|", 1)
            try:
                truth_sessions[aid] = int(cnt)
            except ValueError:
                continue

    expected_ids = {"main", "notes", "assistant"}
    by_id = {}
    for row in data:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            by_id[row["id"]] = row

    found = expected_ids & set(by_id)
    status_ok = 0
    for aid in found:
        if by_id[aid].get("status") == truth_status.get(aid):
            status_ok += 1
    scores["agents_present"] = status_ok / 3.0

    sessions_ok = 0
    for aid in found:
        expected_cnt = truth_sessions.get(aid, 0)
        actual = by_id[aid].get("active_sessions")
        if isinstance(actual, int) and actual == expected_cnt:
            sessions_ok += 1
    scores["session_counts_match"] = sessions_ok / 3.0

    scores["overall_score"] = (
        scores["valid_json"]
        + scores["agents_present"]
        + scores["session_counts_match"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_10_status_json
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
hb_seed_agent notes
hb_seed_agent assistant
mkdir -p /tmp_workspace/results

# Seed deterministic sessions so the grader has a known truth set:
#   main: 2 running, 1 idle
#   notes: 1 running
#   assistant: 0 running
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO sessions (
  agent_id, session_id, source_kind, interactive, created_at,
  last_activity_at, message_count, completed_turn_count, status, type, user_ids
) VALUES
  ('main',      'sess-main-1', 'cli', 1, NOW()::text, NOW()::text, 1, 0, 'running', 'direct', '[]'),
  ('main',      'sess-main-2', 'cli', 1, NOW()::text, NOW()::text, 1, 0, 'running', 'direct', '[]'),
  ('main',      'sess-main-3', 'cli', 1, NOW()::text, NOW()::text, 1, 0, 'idle',    'direct', '[]'),
  ('notes',     'sess-notes-1', 'cli', 1, NOW()::text, NOW()::text, 1, 0, 'running', 'direct', '[]')
ON CONFLICT (agent_id, session_id) DO UPDATE SET status = EXCLUDED.status;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
