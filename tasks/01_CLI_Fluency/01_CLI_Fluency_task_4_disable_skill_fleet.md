---
id: 01_CLI_Fluency_task_4_disable_skill_fleet
name: Disable a skill across the entire fleet
category: 01_CLI_Fluency
timeout_seconds: 240
---

## Prompt

The skill `legacy-mailer` is being retired. Disable it on every agent in the fleet (agents `main`, `notes`, and `assistant` are registered).

You have shell access. The relevant fan-out command is:

```
hermit skills disable legacy-mailer --all
```

After disabling, no agent should have `legacy-mailer` enabled. When done, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `agent_skills` table has no row where `skill_id='legacy-mailer'` and `enabled=true` for any of `main`, `notes`, or `assistant`. The `disable --all` path either removes the wildcard `*` row or writes `enabled=false` rows; both forms satisfy the grader.

## Grading Criteria

- [ ] Zero rows in `agent_skills` where `skill_id='legacy-mailer'` AND `enabled=true`.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"skill_disabled": 0.0, "overall_score": 0.0}

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-c",
             "SELECT count(*) FROM agent_skills "
             "WHERE skill_id='legacy-mailer' AND enabled=true;"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores

    if r.returncode != 0:
        return scores

    try:
        enabled_count = int(r.stdout.strip())
    except ValueError:
        return scores

    if enabled_count == 0:
        scores["skill_disabled"] = 1.0

    scores["overall_score"] = scores["skill_disabled"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_4_disable_skill_fleet
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
hb_seed_agent notes
hb_seed_agent assistant

# Register the legacy-mailer skill in the global registry and enable it on
# every agent. SQL runs against the live (migrated) schema after the gateway
# is healthy.
PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO skills (id, name, description, path, metadata, created_at, updated_at)
VALUES ('legacy-mailer', 'Legacy Mailer', 'Deprecated email skill', '/opt/skills/legacy-mailer', '{}', NOW()::text, NOW()::text)
ON CONFLICT (id) DO NOTHING;

INSERT INTO agent_skills (agent_id, skill_id, enabled, created_at)
VALUES
  ('*',         'legacy-mailer', true, NOW()::text),
  ('main',      'legacy-mailer', true, NOW()::text),
  ('notes',     'legacy-mailer', true, NOW()::text),
  ('assistant', 'legacy-mailer', true, NOW()::text)
ON CONFLICT (agent_id, skill_id) DO UPDATE SET enabled = true;
SQL
```

## Env

```
OPENROUTER_API_KEY
```
