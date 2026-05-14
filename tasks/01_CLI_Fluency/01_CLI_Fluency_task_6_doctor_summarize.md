---
id: 01_CLI_Fluency_task_6_doctor_summarize
name: Run hermit doctor and summarize failures
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

Run `hermit doctor` and write a short summary of any failed checks to `/tmp_workspace/results/doctor.md`. Create the `results` directory if it does not exist.

You have shell access. The relevant commands are:

```
hermit doctor
mkdir -p /tmp_workspace/results
```

Each `hermit doctor` line that starts with a cross mark is a failed check; include the check label in your summary. When done, reply with `DONE`.

## Expected Behavior

After the agent finishes, the file `/tmp_workspace/results/doctor.md` exists, is non-empty, and mentions at least one of the failing checks (`Docker` is always failing in this container since docker is not installed).

## Grading Criteria

- [ ] File `/tmp_workspace/results/doctor.md` exists.
- [ ] File mentions `Docker` (the failing check label).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {"file_exists": 0.0, "mentions_docker": 0.0, "overall_score": 0.0}

    path = os.path.join(workspace_path, "results", "doctor.md")
    if not os.path.isfile(path):
        return scores

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
    except OSError:
        return scores

    if body.strip():
        scores["file_exists"] = 1.0
    if "Docker" in body or "docker" in body:
        scores["mentions_docker"] = 1.0

    scores["overall_score"] = (scores["file_exists"] + scores["mentions_docker"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_6_doctor_summarize
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results
```

## Env

```
OPENROUTER_API_KEY
```
