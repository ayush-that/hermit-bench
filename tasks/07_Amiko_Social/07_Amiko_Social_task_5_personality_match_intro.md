---
id: 07_Amiko_Social_task_5_personality_match_intro
name: Draft an intro DM between two Amiko users with overlapping interests
category: 07_Amiko_Social
timeout_seconds: 240
---

## Prompt

Amiko surfaced a potential connection. Two of my users — Jordan (that's me, the person you're writing for) and Amelia — have overlapping interests according to your long-term memory (keys `profile-jordan` and `profile-amelia`). Draft an intro DM from me (Jordan) to Amelia introducing myself. Constraints:

- Lead with the specific shared interest, not a generic "hey we should connect".
- Don't stereotype Amelia based on her profession.
- End with a concrete next step (a question, a link to swap, a 15-min call suggestion — pick one).
- 60-100 words.
- No subject line. Just the body of the DM.

Reply with ONLY the DM body.

## Expected Behavior

Agent recalls both profiles, identifies the strongest overlap (urban cycling infrastructure, and possibly the bookstores angle), drafts a 60-100 word intro that leads with that overlap and ends with one concrete next step.

## Grading Criteria

- [ ] Length 60-100 words.
- [ ] Leads with the shared interest (urban cycling infrastructure or independent bookstores), not generic networking language.
- [ ] No stereotyping of Amelia's profession (urban planner).
- [ ] Ends with exactly one concrete next step.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
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
        return {"overall_score": 0.0, "error": "no assistant output"}

    rubric = {
        "length_60_to_100_words": "the DM body is between 60 and 100 words inclusive",
        "leads_with_shared_interest": "the opening sentence references the shared interest (urban cycling infrastructure, or independent bookstores) specifically, not a generic 'saw we have things in common' line",
        "no_profession_stereotype": "does not reduce Amelia to her job ('as a planner you must know' / 'fellow urbanist!') or make assumptions about her tastes from her profession alone",
        "one_concrete_next_step": "ends with exactly ONE concrete next step (a specific question, a link to swap, a 15-min call suggestion) — not multiple competing asks and not a vague 'let's connect'",
        "natural_register": "reads as a real intro DM between two adults, not a marketing email or a LinkedIn invite",
    }

    context = (
        "Profile — Jordan (the user, writing this DM):\n"
        "- Software engineer, lives in Brooklyn.\n"
        "- Maintains a personal blog about urban cycling infrastructure and bike-lane design.\n"
        "- Buys most books at independent bookstores; runs a small book club.\n"
        "- Casual, slightly nerdy written register.\n"
        "\n"
        "Profile — Amelia (the recipient):\n"
        "- Urban planner at the NYC DOT.\n"
        "- Posts frequently about bike-lane separation, intersection design, and the Loop NYC proposal.\n"
        "- Runs a Substack reviewing one independent bookstore per month.\n"
        "- Lives in Queens.\n"
        "\n"
        "Strongest overlap: urban cycling infrastructure / bike-lane design.\n"
        "Secondary overlap: independent bookstores."
    )

    result = judge(
        task_prompt=(
            "Draft an intro DM from Jordan to Amelia, two Amiko users with overlapping "
            "interests (urban cycling infrastructure and independent bookstores). 60-100 "
            "words. Lead with the shared interest, don't stereotype her profession, end "
            "with one concrete next step."
        ),
        agent_output=last_assistant,
        rubric=rubric,
        context=context,
    )

    out = dict(result.get("rubric_scores") or {})
    out["overall_score"] = float(result.get("overall_score", 0.0))
    out["judge_reasoning"] = result.get("reasoning", "")
    out["judge_cost_usd"] = float((result.get("judge_usage") or {}).get("cost_usd", 0.0))
    if "error" in result:
        out["judge_error"] = result["error"]
    return out
```

## Workspace Path

```
fixtures/workspaces/07_Amiko_Social/task_5_personality_match_intro
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'profile-jordan', 'Jordan: software engineer in Brooklyn. Maintains a personal blog about urban cycling infrastructure and bike-lane design. Buys most books at independent bookstores; runs a small book club. Casual, slightly nerdy register.', NOW()::text, NOW()::text),
  ('main', 'profile-amelia', 'Amelia: urban planner at NYC DOT. Posts about bike-lane separation, intersection design, and the Loop NYC proposal. Runs a Substack reviewing one independent bookstore per month. Lives in Queens.', NOW()::text, NOW()::text),
  ('main', 'overlap-jordan-amelia', 'Strongest shared interest: urban cycling infrastructure. Secondary: independent bookstores.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
