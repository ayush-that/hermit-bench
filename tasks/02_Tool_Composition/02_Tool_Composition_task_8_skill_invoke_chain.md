---
id: 02_Tool_Composition_task_8_skill_invoke_chain
name: Apply an installed skill to produce a structured digest
category: 02_Tool_Composition
timeout_seconds: 300
---

## Prompt

The skill `standup-digest` is registered and enabled on this agent. It describes how to convert raw standup notes into a digest with three sections: `## Yesterday`, `## Today`, `## Blockers`.

Read `/tmp_workspace/standup-notes.md`, apply the `standup-digest` skill's format, and write the resulting digest to `/tmp_workspace/results/digest.md`. The output must contain all three level-2 headings spelled exactly as listed above, in that order.

When the file has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/digest.md` exists and contains the three required level-2 headings in the correct order, each followed by at least one bulleted line.

## Grading Criteria

- [ ] File exists at `/tmp_workspace/results/digest.md`.
- [ ] Contains `## Yesterday`, `## Today`, and `## Blockers` headings.
- [ ] Headings appear in the order Yesterday -> Today -> Blockers.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {
        "file_exists": 0.0,
        "headings_present": 0.0,
        "order_correct": 0.0,
        "overall_score": 0.0,
    }
    path = os.path.join(workspace_path, "results", "digest.md")
    if not os.path.isfile(path):
        return scores
    scores["file_exists"] = 1.0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
    except OSError:
        return scores

    headings = ["## Yesterday", "## Today", "## Blockers"]
    positions = [body.find(h) for h in headings]
    found = [p for p in positions if p >= 0]
    scores["headings_present"] = len(found) / len(headings)
    if all(p >= 0 for p in positions) and positions == sorted(positions):
        scores["order_correct"] = 1.0

    scores["overall_score"] = (
        scores["file_exists"]
        + scores["headings_present"]
        + scores["order_correct"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_8_skill_invoke_chain
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results /opt/skills/standup-digest

# Standup-digest skill: instructs the agent to convert raw notes into a digest
# with three labelled sections: Yesterday, Today, Blockers.
cat > /opt/skills/standup-digest/SKILL.md <<'MD'
---
name: standup-digest
description: Convert raw standup notes into a structured digest with Yesterday / Today / Blockers sections.
---

# Standup Digest Skill

When asked to produce a standup digest, output a markdown document with
exactly three level-2 sections in this order:

## Yesterday
A bulleted list of what was accomplished yesterday.

## Today
A bulleted list of what is planned for today.

## Blockers
A bulleted list of any blockers. If there are no blockers, write `- None.`
MD

# Register and enable the skill on the main agent.
hb_seed_skill main /opt/skills/standup-digest

cat > /tmp_workspace/standup-notes.md <<'NOTES'
yesterday: finished SLAM integration tests, reviewed bob's PR, fixed CI flake on the firmware build
today: pair with carol on R-Series qualification, write the deploy runbook, attend Q1 review at 3pm
blockers: STM32 supplier hasn't confirmed Q2 shipping dates
NOTES
```

## Env

```
OPENROUTER_API_KEY
```
