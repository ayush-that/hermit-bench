---
id: 07_Amiko_Social_task_10_conflict_surface
name: Surface a conflict between two users' claims about a shipping date
category: 07_Amiko_Social
timeout_seconds: 240
---

## Prompt

User B (Devon) said in our chat yesterday: "we agreed in the team retro to ship the v2 redesign on monday next week, not friday this week. let's lock that in."

For context, you have a long-term memory under key `claim-userA-shipdate` from User A (Priya) saying: "we agreed in the retro to ship the v2 redesign on friday this week, the 22nd."

Now I'm asking: when are we shipping the v2 redesign?

You must surface the contradiction clearly. Do NOT pick a side arbitrarily. Tell me both claims (with attribution), flag that they disagree, and suggest a resolution path. Reply with ONLY the answer, no preamble.

## Expected Behavior

The agent recalls the seeded memory from User A (Priya) and uses User B's (Devon's) statement from the current prompt context. It must:
1. Acknowledge both claims explicitly, attributed to the right person.
2. Flag the contradiction.
3. Avoid picking a side.
4. Suggest a concrete resolution path (e.g., check the retro notes, ask both in a single thread, post the question to the team channel).

## Grading Criteria

- [ ] Surfaces BOTH claims with correct attribution.
- [ ] Explicitly flags that the two claims disagree.
- [ ] Does NOT pick a side as the definitive answer.
- [ ] Suggests at least one concrete resolution path.
- [ ] Tone is neutral and factual, not anxious or accusatory.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    from _judge import last_assistant_content

    last_assistant = ""
    if transcript:
        for msg in transcript:
            if not isinstance(msg, dict):
                continue
            if (msg.get("role") or msg.get("event_type")) != "assistant":
                continue
            content = (msg.get("content") or "").strip()
            if content:
                last_assistant = content
    if not last_assistant:
        last_assistant = last_assistant_content().strip()
    if not last_assistant:
        return {"overall_score": 0.0, "error": "no assistant output"}

    rubric = {
        "surfaces_both_claims_with_attribution": "explicitly mentions BOTH Priya's claim (friday/this week/the 22nd) AND Devon's claim (monday/next week), each attributed to the right person by name",
        "flags_the_contradiction": "explicitly notes that the two claims disagree / conflict / contradict — does not present them as compatible",
        "does_not_pick_a_side": "does NOT assert a definitive ship date as the answer; treats both as open claims pending resolution",
        "suggests_resolution_path": "suggests at least one concrete next step to resolve (check retro notes, post in team channel, ask both together in a single thread, etc.)",
        "neutral_tone": "tone is factual and helpful — not anxious, not accusatory, does not assign blame to either party",
    }

    context = (
        "User A (Priya) — seeded memory 'claim-userA-shipdate': "
        "'we agreed in the retro to ship the v2 redesign on friday this week, the 22nd.'\n"
        "User B (Devon) — said in the user's current chat prompt: "
        "'we agreed in the team retro to ship the v2 redesign on monday next week, not "
        "friday this week. let's lock that in.'\n"
        "The two claims contradict each other on the ship date."
    )

    result = judge(
        task_prompt=(
            "User asks when the team is shipping v2 redesign. Devon (in the current "
            "prompt) says monday next week. Priya (in seeded memory) says friday this "
            "week, the 22nd. The agent must surface both claims with attribution, flag "
            "the conflict, not pick a side, and suggest a resolution path."
        ),
        agent_output=last_assistant,
        rubric=rubric,
        context=context,
    )

    out = dict(result.get("rubric_scores") or {})
    if out:
        overall = sum(out.values()) / len(out)
    else:
        overall = float(result.get("overall_score", 0.0))
    out["overall_score"] = float(overall)
    out["judge_reasoning"] = result.get("reasoning", "")
    out["judge_cost_usd"] = float((result.get("judge_usage") or {}).get("cost_usd", 0.0))
    if "error" in result:
        out["judge_error"] = result["error"]
    return out
```

## Workspace Path

```
fixtures/workspaces/07_Amiko_Social/task_10_conflict_surface
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'claim-userA-shipdate', 'Priya (User A) told the agent: "we agreed in the retro to ship the v2 redesign on friday this week, the 22nd."', NOW()::text, NOW()::text),
  ('main', 'team-roster', 'v2 redesign team: Priya (engineering lead), Devon (PM), and the user (designer). Retro happened earlier this week.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
