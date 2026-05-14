---
id: 01_CLI_Fluency_task_9_setup_wizard_idempotent
name: Set and verify an agent config value
category: 01_CLI_Fluency
timeout_seconds: 180
---

## Prompt

Set the agent `main` model temperature to `0.2` using the `hermit config` CLI, then verify the value was written by reading it back and saving it to `/tmp_workspace/results/temperature.txt`.

You have shell access. The relevant commands are:

```
hermit config --agent main set model.temperature 0.2
hermit config --agent main get model.temperature > /tmp_workspace/results/temperature.txt
```

When done, reply with `DONE`.

## Expected Behavior

The `config_json` stored for agent `main` reflects `model.temperature = 0.2`, and the file `/tmp_workspace/results/temperature.txt` contains `0.2` (possibly with a trailing newline).

Note: The original plan called for re-running `hermit setup` non-interactively, but `hermit setup` is a fully interactive TUI with no non-interactive flag, so this task exercises the equivalent idempotent `config set` / `config get` round-trip instead.

## Grading Criteria

- [ ] `agents.config_json` JSON contains `model.temperature == 0.2`.
- [ ] File `/tmp_workspace/results/temperature.txt` contains `0.2`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import json, os, subprocess
    scores = {"config_set": 0.0, "file_written": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c",
             "SELECT config_json FROM agents WHERE agent_id='main';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        r = None

    if r is not None and r.returncode == 0 and r.stdout.strip():
        try:
            cfg = json.loads(r.stdout.strip())
            temp = cfg.get("model", {}).get("temperature")
            if isinstance(temp, (int, float)) and abs(float(temp) - 0.2) < 1e-9:
                scores["config_set"] = 1.0
        except (json.JSONDecodeError, AttributeError):
            pass

    path = os.path.join(workspace_path, "results", "temperature.txt")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                body = f.read().strip()
            if body == "0.2":
                scores["file_written"] = 1.0
        except OSError:
            pass

    scores["overall_score"] = (scores["config_set"] + scores["file_written"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_9_status_text
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
