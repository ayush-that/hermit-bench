---
id: 07_Amiko_Social_task_1_draft_post_from_thought
name: Draft a post from a one-sentence thought in user's voice
category: 07_Amiko_Social
timeout_seconds: 240
---

## Prompt

I had a thought I want to turn into a post: "Most product roadmaps are wishlists pretending to be plans." Draft me a 60-120 word Amiko post in my voice. Use my three most recent posts as voice samples (they're seeded in your long-term memory under keys starting with `voice-sample-`). Reply with ONLY the post body — no preamble, no quotation marks, no hashtags.

## Expected Behavior

The agent recalls the three `voice-sample-*` memories, infers the user's voice (lowercase, short sentences, no emojis, mild irreverence), and produces a 60-120 word post that captures the original thought without clichés.

## Grading Criteria

- [ ] Output is 60-120 words.
- [ ] Tone matches the seeded voice samples (lowercase prose, short sentences, no emojis).
- [ ] Captures the original thought ("roadmaps as wishlists").
- [ ] No clichés or generic startup-LinkedIn phrasing.
- [ ] No quotation marks, no preamble.

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
        "length_60_to_120_words": "the post is between 60 and 120 words inclusive",
        "voice_match_lowercase": "reads as lowercase prose, short sentences, no emojis, mild irreverence",
        "captures_original_thought": "the post is clearly about roadmaps being wishlists rather than plans",
        "no_cliches": "does not use phrases like 'in today's world', 'at the end of the day', 'game-changer', or other LinkedIn cliches",
        "no_preamble_or_quotes": "the response is the post body only, no 'here is your post', no surrounding quotes",
    }

    voice_samples = (
        "Voice samples to match:\n"
        "1. half of \"strategy\" is just having the courage to say no to things that look profitable.\n"
        "2. shipping is a habit, not an event. teams that ship on tuesday ship on friday too.\n"
        "3. the founders i trust most talk about their product the way a chef talks about their knives.\n"
        "Notice: lowercase, short, opinionated, no emojis, no hashtags."
    )

    result = judge(
        task_prompt=(
            "Draft a 60-120 word Amiko post in the user's voice based on the thought: "
            "'Most product roadmaps are wishlists pretending to be plans.' Reply with only "
            "the post body."
        ),
        agent_output=last_assistant,
        rubric=rubric,
        context=voice_samples,
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
fixtures/workspaces/07_Amiko_Social/task_1_draft_post_from_thought
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'voice-sample-1', 'half of "strategy" is just having the courage to say no to things that look profitable.', NOW()::text, NOW()::text),
  ('main', 'voice-sample-2', 'shipping is a habit, not an event. teams that ship on tuesday ship on friday too.', NOW()::text, NOW()::text),
  ('main', 'voice-sample-3', 'the founders i trust most talk about their product the way a chef talks about their knives.', NOW()::text, NOW()::text),
  ('main', 'voice-style-notes', 'User writes in lowercase, short sentences, no emojis, no hashtags, mildly contrarian about startup culture.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
