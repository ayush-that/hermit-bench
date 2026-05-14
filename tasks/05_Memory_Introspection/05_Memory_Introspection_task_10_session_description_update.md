---
id: 05_Memory_Introspection_task_10_session_description_update
name: Update session description via introspection
category: 05_Memory_Introspection
timeout_seconds: 240
---

## Prompt

We just spent a long stretch talking about the Q1 budget — projected revenue, headcount costs, marketing spend, and the office-renovation line item. If you were going to relabel this session for future-you, what would you call it? Propose a one-line description that mentions `Q1 budget`. Reply with just the description on a single line.

## Expected Behavior

The `session_description_update` tool is introspection-only — not in the main agent's toolset — so we grade the agent's proposed description text instead. The runtime sets `sessions.description` from the user's first message via the `fallback` source; the seed forces it to a known stale label, and the grader checks BOTH:

1. the assistant's response proposes a label containing `Q1 budget`, and
2. *or* the live `sessions.description` was updated by the runtime to contain `Q1 budget` (covers the case where future harness work wires the checkpoint trigger).

Either signal scores the criterion. The session-description hook path lives in `apps/agent/src/tools/session-description.ts`.

## Grading Criteria

- [ ] Either the assistant's reply or the active session's `description` column contains `Q1 budget` (case-insensitive).

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os, subprocess
    scores = {"q1_budget_proposed": 0.0, "overall_score": 0.0}
    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"

    # Path A: session.description in DB mentions Q1 budget (introspection wrote it).
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At",
             "-c",
             "SELECT COALESCE(description,'') FROM sessions "
             "WHERE agent_id='main' AND session_id LIKE 'cli:%' "
             "ORDER BY last_activity_at DESC LIMIT 1;"],
            capture_output=True, text=True, env=env, timeout=15,
        )
        if r.returncode == 0 and "q1 budget" in (r.stdout or "").lower():
            scores["q1_budget_proposed"] = 1.0
    except Exception:
        pass

    # Path B: assistant text contains Q1 budget.
    if scores["q1_budget_proposed"] == 0.0:
        try:
            r = subprocess.run(
                ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
                 "-At",
                 "-c",
                 "SELECT string_agg(content, ' || ') FROM session_events "
                 "WHERE agent_id='main' AND event_type='assistant' "
                 "AND content IS NOT NULL;"],
                capture_output=True, text=True, env=env, timeout=15,
            )
            if r.returncode == 0 and "q1 budget" in (r.stdout or "").lower():
                scores["q1_budget_proposed"] = 1.0
        except Exception:
            pass

    scores["overall_score"] = scores["q1_budget_proposed"]
    return scores
```

## Workspace Path

```
fixtures/workspaces/05_Memory_Introspection/task_10_session_description_update
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
