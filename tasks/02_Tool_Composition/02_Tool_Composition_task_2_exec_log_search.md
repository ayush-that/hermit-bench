---
id: 02_Tool_Composition_task_2_exec_log_search
name: Find a needle in a haystack of logs
category: 02_Tool_Composition
timeout_seconds: 240
---

## Prompt

Somewhere under `/tmp_workspace/logs/` there is exactly one line of the form `KEY_FOUND=<number>`. The directory contains 200 log files; you do not know which one holds the line.

Find that line, extract the number, and write only the number (no trailing whitespace, no other text) to `/tmp_workspace/results/key.txt`.

You have shell access via the `exec` tool. `grep`, `find`, and other standard Unix utilities are available.

When the file has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/key.txt` exists and contains the number `42`.

## Grading Criteria

- [ ] File `/tmp_workspace/results/key.txt` exists.
- [ ] Its trimmed contents equal `42`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {"file_exists": 0.0, "value_correct": 0.0, "overall_score": 0.0}
    path = os.path.join(workspace_path, "results", "key.txt")
    if not os.path.isfile(path):
        return scores
    scores["file_exists"] = 1.0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read().strip()
    except OSError:
        return scores
    if body == "42":
        scores["value_correct"] = 1.0
    scores["overall_score"] = (scores["file_exists"] + scores["value_correct"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_2_exec_log_search
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/logs /tmp_workspace/results

# Generate 200 deterministic log files. Place the needle (KEY_FOUND=42) in
# logs/file_137.log on a known line so the agent must search the directory
# tree rather than guessing.
for i in $(seq 1 200); do
  {
    for j in $(seq 1 20); do
      echo "INFO file_${i} line ${j} routine entry"
    done
  } > "/tmp_workspace/logs/file_${i}.log"
done
sed -i '10s/.*/KEY_FOUND=42 special marker/' /tmp_workspace/logs/file_137.log
```

## Env

```
OPENROUTER_API_KEY
```
