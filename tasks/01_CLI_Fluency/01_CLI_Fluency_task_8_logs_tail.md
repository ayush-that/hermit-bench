---
id: 01_CLI_Fluency_task_8_logs_tail
name: Extract ERROR lines from a gateway log
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

A captured gateway log is sitting at `/tmp_workspace/gateway.log` (100 lines). Read the last 50 lines and save every line that contains the substring `ERROR` to `/tmp_workspace/results/errors.txt`. One ERROR line per output line, preserving the original text.

You have shell access. Standard Unix tools (`tail`, `grep`) are available.

When the file has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/errors.txt` exists and contains the three ERROR lines that appear in the last 50 lines of the log:

```
ERROR auth: invalid bearer token
ERROR db: connection reset by peer
ERROR scheduler: cron expression failed to parse
```

## Grading Criteria

- [ ] All three expected ERROR lines are present in `/tmp_workspace/results/errors.txt`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {"errors_extracted": 0.0, "overall_score": 0.0}

    expected = [
        "ERROR auth: invalid bearer token",
        "ERROR db: connection reset by peer",
        "ERROR scheduler: cron expression failed to parse",
    ]
    path = os.path.join(workspace_path, "results", "errors.txt")
    if not os.path.isfile(path):
        return scores

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
    except OSError:
        return scores

    matched = sum(1 for line in expected if line in body)
    scores["errors_extracted"] = matched / len(expected)
    scores["overall_score"] = scores["errors_extracted"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_8_logs_tail
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

# Build a 100-line log: 47 INFO lines, then the 3 ERROR lines we want
# extracted, then 50 more INFO lines so the ERRORs land inside the last 50.
{
  for i in $(seq 1 47); do
    echo "INFO line $i"
  done
  echo "ERROR auth: invalid bearer token"
  echo "ERROR db: connection reset by peer"
  echo "ERROR scheduler: cron expression failed to parse"
  for i in $(seq 51 100); do
    echo "INFO line $i"
  done
} > /tmp_workspace/gateway.log
```

## Env

```
OPENROUTER_API_KEY
```
