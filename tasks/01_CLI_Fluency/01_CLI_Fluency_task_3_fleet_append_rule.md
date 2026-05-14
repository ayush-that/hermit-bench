---
id: 01_CLI_Fluency_task_3_fleet_append_rule
name: Append a rule to every agent's instructions
category: 01_CLI_Fluency
timeout_seconds: 240
---

## Prompt

Append the rule `Never share customer email addresses.` to the `rules` instruction of *every* agent in the fleet. There are three agents: `main`, `notes`, and `assistant`.

You have shell access. The relevant fan-out command is:

```
hermit instructions append rules "Never share customer email addresses." --all
```

When you have appended the rule to every agent's `rules` instruction, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `instructions.content` for `key='rules'` on each of `main`, `notes`, and `assistant` contains the substring `Never share customer email addresses.`.

## Grading Criteria

- [ ] All three agents have a `rules` row.
- [ ] Each `rules` row's content includes the new sentence.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"agents_have_rule": 0.0, "overall_score": 0.0}
    target_sentence = "Never share customer email addresses."

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "\t",
             "-c",
             "SELECT agent_id, content FROM instructions "
             "WHERE key='rules' AND agent_id IN ('main','notes','assistant');"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0:
        return scores

    matched = set()
    for line in r.stdout.strip().splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        agent_id, content = parts
        if target_sentence in content:
            matched.add(agent_id)

    expected = {"main", "notes", "assistant"}
    scores["agents_have_rule"] = len(matched & expected) / 3.0
    scores["overall_score"] = scores["agents_have_rule"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_3_fleet_append_rule
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
hb_seed_agent notes
hb_seed_agent assistant
# Seed each agent with an initial `rules` instruction so append has a baseline.
hb_seed_instruction main      rules "Be polite."
hb_seed_instruction notes     rules "Be concise."
hb_seed_instruction assistant rules "Be helpful."
```

## Env

```
OPENROUTER_API_KEY
```
