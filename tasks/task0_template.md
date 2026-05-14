---
id: <category>_task_<N>_<short_name>
name: Human-readable task name
category: <category>
timeout_seconds: 300
---

## Prompt

The task instruction sent to the agent. Write it as if speaking directly to the agent.
Workspace files (including any task data) are mounted at `/tmp_workspace/`.

**Important:** Do NOT use `##` (level-2 headings) inside the Prompt section. The parser splits sections by `##` headings. Use `###` or lower for any sub-headings within the prompt.

## Expected Behavior

Human-only description of what a correct run looks like.

## Grading Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    """
    Runs inside the container after the agent finishes. Has access to:
    - /tmp_workspace/ (mounted host workspace + agent writes)
    - Postgres at 127.0.0.1:5432 (db=hermit, user=hermit, password=hermit)
    - `transcript` is the parsed gateway transcript (list of {role, content}).

    Return a dict of metric -> float in [0, 1]. Must include "overall_score".
    """
    scores = {"overall_score": 0.0}
    return scores
```

## Workspace Path

```
fixtures/workspaces/<category>/<task_dir>
```

## Seed SQL

```sql
-- Optional. Applied before gateway boot. Use to insert rows into the hermit DB
-- (users, memories, instructions, agent_skills, agent_policies, schedules, ...).
-- See docs/seed-format.md for verified table/column names.
```

## Seed Post

```bash
# Optional. Runs after the gateway is healthy. Use for `hermit ...` CLI seeding
# via /usr/local/bin/seed_helpers.sh (source it to get hb_seed_* helpers).
```

## Env

```
# Env var names whose values are forwarded into the container from the host .env.
OPENROUTER_API_KEY
```

<!--
=== Field Reference ===

Frontmatter (YAML):
  - id:              Unique task identifier (must match filename pattern)
  - name:            Human-readable name
  - category:        One of: 01_CLI_Fluency, 02_Tool_Composition,
                     03_Access_Control, 04_Channel_Routing,
                     05_Memory_Introspection, 06_Scheduling_Automation
  - timeout_seconds: Max wall-clock time for the agent (default: 300)

Sections (all parsed by src/utils/task_parser.py):
  - ## Prompt              Task instruction sent to the agent (required)
  - ## Expected Behavior   Human-readable description of correct behavior
  - ## Grading Criteria    Checklist of what is evaluated
  - ## Automated Checks    Python grading function executed inside the container
  - ## Workspace Path      Relative path to the task data directory (required)
  - ## Seed SQL            Raw SQL applied before gateway boots
  - ## Seed Post           Bash script run after gateway is healthy
  - ## Env                 Env var names to forward into the container
-->
