---
id: 06_Scheduling_Automation_task_9_schedule_with_prompt_var
name: Schedule whose prompt references last-week's date range
category: 06_Scheduling_Automation
timeout_seconds: 240
---

## Prompt

Create a cron schedule that runs every Monday at 09:00 UTC and asks you to generate a status report covering last week's date range.

Use the `schedule_create` tool with:

- `type`: `"cron"`
- `cron_expression`: `"0 9 * * MON"`
- `id`: `"weekly-status"`
- `prompt`: a one-sentence instruction that tells the future agent to compute "last week" itself. The prompt must contain BOTH the substring `last week` (case-insensitive) AND a placeholder-style marker so the future agent knows it's expected to fill in the date range. Use double-curly placeholders, for example: `"Generate a status report for last week ({{prev_week_range}})."`

Call the tool exactly once. After it succeeds, reply with `DONE`.

## Expected Behavior

A new row in `schedules` for `(main, weekly-status)` with `type='cron'`, `cron_expression='0 9 * * MON'`, and a `prompt` containing both `last week` (case-insensitive) and a `{{...}}` style placeholder.

## Grading Criteria

- [ ] Row exists with correct cron expression.
- [ ] Prompt contains a `{{ … }}` placeholder.
- [ ] Prompt mentions `last week` (case-insensitive).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, re, subprocess
    scores = {
        "row_correct": 0.0,
        "placeholder_present": 0.0,
        "last_week_mentioned": 0.0,
        "overall_score": 0.0,
    }

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    r = subprocess.run(
        ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
         "-At", "-F", "|", "-c",
         "SELECT cron_expression, prompt FROM schedules "
         "WHERE agent_id='main' AND schedule_id='weekly-status';"],
        capture_output=True, text=True, env=env, timeout=15,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return scores
    parts = r.stdout.strip().split("|", 1)
    if len(parts) < 2:
        return scores
    cron_expr, prompt = parts[0], parts[1]

    norm = re.sub(r"\s+", " ", cron_expr.strip()).upper()
    if norm in ("0 9 * * MON", "0 9 * * 1"):
        scores["row_correct"] = 1.0
    if re.search(r"\{\{[^}]+\}\}", prompt):
        scores["placeholder_present"] = 1.0
    if "last week" in prompt.lower():
        scores["last_week_mentioned"] = 1.0

    scores["overall_score"] = (
        scores["row_correct"]
        + scores["placeholder_present"]
        + scores["last_week_mentioned"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/06_Scheduling_Automation/task_9_schedule_with_prompt_var
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
