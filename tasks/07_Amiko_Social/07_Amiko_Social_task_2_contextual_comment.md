---
id: 07_Amiko_Social_task_2_contextual_comment
name: Draft a substantive comment on a specific post
category: 07_Amiko_Social
timeout_seconds: 240
---

## Prompt

I want to engage with this Amiko post from @maren_b — read it and draft me a substantive comment to leave. Reply with ONLY the comment text, no preamble.

Post by @maren_b:
"three weeks of using cursor full-time and i think the productivity gains are real but uneven. it crushes anything ts-shaped — types, refactors, boilerplate. it limps on anything that requires holding a domain model in your head. the dangerous part is that the limping doesn't feel different from the crushing while you're in it."

My known opinions (in your long-term memory under keys starting with `opinion-`): I believe AI tools amplify existing engineering judgment rather than replace it, and I've publicly disagreed with the "10x productivity" framing.

## Expected Behavior

The agent recalls the seeded opinions, drafts a comment under 50 words that (a) references something specific from maren's post (not generic praise), (b) aligns with the user's stance that AI amplifies rather than replaces judgment, (c) avoids "great post!" / "this!" / clichés.

## Grading Criteria

- [ ] Comment is under 50 words.
- [ ] References something specific from maren's post (the limping/crushing dichotomy, ts-shaped tasks, domain model).
- [ ] Aligns with user's known opinion that AI amplifies judgment, not replaces it.
- [ ] No generic praise ("great post!", "this!", "100%", "so true").
- [ ] Reads as a real comment, not a marketing reply.

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
        "under_50_words": "the comment is 50 words or fewer",
        "references_specific_detail": "the comment names a specific element of maren's post (the limping/crushing dichotomy, ts-shaped tasks, holding a domain model, etc.) rather than reacting to the post in the abstract",
        "aligns_with_user_opinion": "the comment is consistent with the view that AI tools amplify existing engineering judgment rather than replace it; does not contradict that stance",
        "no_generic_praise": "does NOT use 'great post', 'this!', '100%', 'so true', 'totally agree', or similar empty praise phrases",
        "sounds_like_a_real_comment": "reads as a genuine peer comment, not corporate marketing or an essay; conversational register",
    }

    context = (
        "User's seeded opinions:\n"
        "- AI tools amplify existing engineering judgment rather than replace it.\n"
        "- The '10x productivity' framing is overstated and the user has publicly disagreed with it.\n"
    )

    result = judge(
        task_prompt=(
            "Draft a comment under 50 words on maren_b's post about cursor's productivity "
            "gains being real but uneven. The comment should reference something specific "
            "from the post and align with the user's view that AI amplifies rather than "
            "replaces engineering judgment."
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
fixtures/workspaces/07_Amiko_Social/task_2_contextual_comment
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'opinion-ai-amplifies', 'User believes AI tools amplify existing engineering judgment rather than replace it. Cursor and Copilot help senior engineers more than they help juniors.', NOW()::text, NOW()::text),
  ('main', 'opinion-anti-10x', 'User has publicly disagreed with the "10x productivity from AI" framing. Considers it marketing, not measurement.', NOW()::text, NOW()::text),
  ('main', 'opinion-tools-not-replacements', 'User repeatedly says good tools should sharpen taste, not paper over its absence.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
