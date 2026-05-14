---
id: 06_Scheduling_Automation_task_4_list_recent_runs
name: List the 5 most-recent runs of a schedule as markdown
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

Show the user the 5 most-recent runs of the schedule `weekly-release-notes`.

Use the `schedule_runs` tool with `id`: `"weekly-release-notes"` and `limit`: `5`. Then format the result as a markdown table with the columns `Run ID`, `Status`, `Started At`. Save the table to `/tmp_workspace/results/runs.md`. The file must have exactly 5 data rows (plus the header and separator rows).

When the file has been written, reply with `DONE`.

## Expected Behavior

`/tmp_workspace/results/runs.md` contains a markdown table with 5 data rows. The 5 rows correspond to the 5 most-recent rows in `schedule_runs` ordered by `started_at DESC`.

## Grading Criteria

- [ ] File exists and parses as a markdown table with ≥5 data rows.
- [ ] Statuses of the 5 rows match the 5 most-recent `schedule_runs.status` values for `weekly-release-notes` (set equality).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess, re
    scores = {
        "file_exists": 0.0,
        "row_count": 0.0,
        "statuses_match": 0.0,
        "overall_score": 0.0,
    }

    path = os.path.join(workspace_path, "results", "runs.md")
    if not os.path.isfile(path):
        return scores
    scores["file_exists"] = 1.0

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return scores

    # Parse markdown rows: lines starting with '|' that are not the separator.
    sep_re = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")
    data_rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if sep_re.match(stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        # Skip the header row (heuristic: lowercase 'status' as a header word).
        if any(c.lower() in {"status", "run id", "started at", "started"} for c in cells):
            continue
        data_rows.append(cells)

    if len(data_rows) >= 5:
        scores["row_count"] = 1.0

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    r = subprocess.run(
        ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
         "-At", "-c",
         "SELECT status FROM schedule_runs "
         "WHERE agent_id='main' AND schedule_id='weekly-release-notes' "
         "ORDER BY started_at DESC LIMIT 5;"],
        capture_output=True, text=True, env=env, timeout=15,
    )
    expected = [s.strip() for s in (r.stdout or "").splitlines() if s.strip()]

    # Compare as multiset of statuses across the agent's first 5 data rows.
    if expected and len(data_rows) >= 5:
        seen = []
        for row in data_rows[:5]:
            for cell in row:
                low = cell.lower().strip()
                if low in {"success", "failed", "running", "pending", "error", "ok"}:
                    seen.append(low)
                    break
        # Normalise "error" -> "failed" and "ok" -> "success" for tolerance.
        norm = {"error": "failed", "ok": "success"}
        seen_n = sorted(norm.get(s, s) for s in seen)
        exp_n = sorted(norm.get(s, s) for s in expected)
        if seen_n == exp_n and seen_n:
            scores["statuses_match"] = 1.0

    scores["overall_score"] = (
        scores["file_exists"]
        + scores["row_count"]
        + scores["statuses_match"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_4_list_recent_runs
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO schedules (
  agent_id, schedule_id, type, status, cron_expression, prompt,
  session_mode, delivery, policy, created_at, updated_at, run_count, consecutive_errors
) VALUES (
  'main', 'weekly-release-notes', 'cron', 'active', '0 17 * * FRI',
  'Generate this week''s release notes.',
  'dedicated', '{"kind":"silent"}'::jsonb, '{}'::jsonb,
  NOW()::text, NOW()::text, 10, 0
) ON CONFLICT (agent_id, schedule_id) DO NOTHING;

-- Seed exactly 10 runs: 5 success, 5 failed, monotonically increasing started_at.
INSERT INTO schedule_runs (agent_id, schedule_id, status, prompt, started_at, finished_at, duration_ms, error)
VALUES
  ('main', 'weekly-release-notes', 'success', 'gen', (NOW() - INTERVAL '10 hours')::text, (NOW() - INTERVAL '10 hours')::text, 1200, NULL),
  ('main', 'weekly-release-notes', 'failed',  'gen', (NOW() - INTERVAL '9 hours')::text,  (NOW() - INTERVAL '9 hours')::text,  900,  'mock error A'),
  ('main', 'weekly-release-notes', 'success', 'gen', (NOW() - INTERVAL '8 hours')::text,  (NOW() - INTERVAL '8 hours')::text,  1100, NULL),
  ('main', 'weekly-release-notes', 'failed',  'gen', (NOW() - INTERVAL '7 hours')::text,  (NOW() - INTERVAL '7 hours')::text,  800,  'mock error B'),
  ('main', 'weekly-release-notes', 'success', 'gen', (NOW() - INTERVAL '6 hours')::text,  (NOW() - INTERVAL '6 hours')::text,  1000, NULL),
  ('main', 'weekly-release-notes', 'failed',  'gen', (NOW() - INTERVAL '5 hours')::text,  (NOW() - INTERVAL '5 hours')::text,  900,  'mock error C'),
  ('main', 'weekly-release-notes', 'success', 'gen', (NOW() - INTERVAL '4 hours')::text,  (NOW() - INTERVAL '4 hours')::text,  1100, NULL),
  ('main', 'weekly-release-notes', 'failed',  'gen', (NOW() - INTERVAL '3 hours')::text,  (NOW() - INTERVAL '3 hours')::text,  900,  'mock error D'),
  ('main', 'weekly-release-notes', 'success', 'gen', (NOW() - INTERVAL '2 hours')::text,  (NOW() - INTERVAL '2 hours')::text,  1200, NULL),
  ('main', 'weekly-release-notes', 'failed',  'gen', (NOW() - INTERVAL '1 hour')::text,   (NOW() - INTERVAL '1 hour')::text,   900,  'mock error E');
SQL
```

## Env

```
OPENROUTER_API_KEY
```
