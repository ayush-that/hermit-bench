---
id: 08_Amiko_Pipelines_task_8_share_copy
name: Draft 3 platform-specific share-copy variants for a milestone event
category: 08_Amiko_Pipelines
timeout_seconds: 240
---

## Prompt

You are the user's Amiko digital twin. Their post "most roadmaps are wishlists pretending to be plans" just hit 100 likes on Amiko — a small milestone, but worth sharing. Draft 3 share-copy variants the user could publish, one per platform.

The user's voice is in long-term memory:
- `voice-style-notes` — overall style
- `voice-sample-1`, `voice-sample-2`, `voice-sample-3` — three of their past posts you can model on

Write with the person's real voice. Be specific, self-aware, shareable. Avoid generic product copy, personality-report labels, and AI-assistant phrasing. Do not explain the product. Do not reference deceased relatives, estrangement, childhood trauma, divorce, addiction, mental health diagnoses, or politics — this is public.

Output ONLY JSON in this shape, no preamble, no markdown fences:

```
{
  "twitter": "<tweet, ≤280 chars including any [link] placeholder, must include [link]>",
  "threads": "<threads post, ≤500 chars, can be slightly longer/looser than the tweet, must include [link]>",
  "telegram": "<telegram message for a small private group of close friends/peers — casual, can be 2-4 short lines, no [link] requirement, no hashtags>"
}
```

Platform fit rules:
- **twitter**: punchy, ≤280 chars, ends on a hook or a quotable line, include `[link]`. No hashtags (the user doesn't use them).
- **threads**: slightly longer/looser, ≤500 chars, can have a second sentence that develops the thought. Include `[link]`. No hashtags.
- **telegram**: casual private-channel tone. Can be more honest/self-deprecating since it's a small group. 2-4 short lines, no `[link]`, no hashtags. This is the "told my friends" version.

All 3 must be DISTINCT — not three rewrites of the same sentence with different lengths. Each should pull a different angle from the milestone (the post itself, the surprise of it landing, the contrast with prior attempts that didn't, etc.).

## Expected Behavior

The agent recalls the seeded voice samples, drafts 3 platform-appropriate variants that match the user's lowercase contrarian voice, all distinct in angle (not length-rewrites of the same line), no hashtags, no AI-assistant clichés, no product explanation.

## Grading Criteria

- [ ] Valid JSON with exactly the 3 keys (twitter, threads, telegram).
- [ ] twitter ≤280 chars and contains `[link]`.
- [ ] threads ≤500 chars and contains `[link]`.
- [ ] telegram is casual (2-4 short lines), no `[link]`, no hashtags.
- [ ] All 3 are distinct angles, not the same sentence reformatted.
- [ ] Voice matches the seeded samples (lowercase, contrarian, no emojis/exclamations).
- [ ] No AI-assistant clichés ("excited to share", "humbled to announce", "thrilled that").
- [ ] No hashtags anywhere.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import json as _json
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

    # Parse to compute deterministic length / placeholder checks
    parsed = None
    tw_len = th_len = tg_len = -1
    tw_has_link = th_has_link = False
    tg_has_link = tg_has_hash = False
    any_hashtag = False
    try:
        cleaned = last_assistant.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.rsplit("```", 1)[0].strip()
        parsed = _json.loads(cleaned)
        if isinstance(parsed, dict):
            tw = str(parsed.get("twitter", ""))
            th = str(parsed.get("threads", ""))
            tg = str(parsed.get("telegram", ""))
            tw_len, th_len, tg_len = len(tw), len(th), len(tg)
            tw_has_link = "[link]" in tw
            th_has_link = "[link]" in th
            tg_has_link = "[link]" in tg
            tg_has_hash = "#" in tg
            any_hashtag = "#" in tw or "#" in th or "#" in tg
    except Exception:
        pass

    rubric = {
        "valid_json_three_keys": "output parses as JSON object with exactly the three keys: twitter, threads, telegram (no extras, all present)",
        "twitter_constraints": f"twitter is ≤280 chars (actual={tw_len}) AND contains the [link] placeholder (actual={tw_has_link})",
        "threads_constraints": f"threads is ≤500 chars (actual={th_len}) AND contains the [link] placeholder (actual={th_has_link})",
        "telegram_casual_no_link": f"telegram is 2-4 short lines (casual private register), does NOT contain [link] (actual={tg_has_link}), does NOT contain hashtags (actual_hash={tg_has_hash})",
        "all_three_distinct_angles": "the three variants pull different angles on the milestone — not three length-variations of the same sentence; each has a unique opening move or framing",
        "matches_user_voice": "voice matches the seeded samples: lowercase or near-lowercase, contrarian edge intact, no emojis, no exclamation marks, no LinkedIn-startup register",
        "no_ai_assistant_cliches": "does NOT use phrases like 'excited to share', 'humbled to announce', 'thrilled that', 'grateful for the support', 'this means so much'",
        "no_hashtags_anywhere": f"no hashtags appear in any variant (deterministic: any_hashtag={any_hashtag})",
        "no_product_explanation": "does NOT explain what Amiko is, what likes mean, or otherwise pitch the product to the reader",
    }

    context = (
        "User voice samples:\n"
        "- 'half of strategy is just having the courage to say no to things that look profitable.'\n"
        "- 'shipping is a habit, not an event. teams that ship on tuesday ship on friday too.'\n"
        "- 'the founders i trust most talk about their product the way a chef talks about their knives.'\n"
        "Voice style notes: lowercase, short sentences, no emojis, no hashtags, mildly contrarian about startup culture.\n"
        "\n"
        "Event being shared: the user's post 'most roadmaps are wishlists pretending to be plans' hit 100 likes on Amiko — modest milestone.\n"
        "\n"
        f"Parsed lengths: twitter={tw_len}, threads={th_len}, telegram={tg_len}.\n"
        f"Has [link]: twitter={tw_has_link}, threads={th_has_link}, telegram={tg_has_link}.\n"
        f"Any hashtag anywhere: {any_hashtag}."
    )

    result = judge(
        task_prompt=(
            "Draft 3 share-copy variants (twitter ≤280 chars +[link], threads ≤500 chars "
            "+[link], telegram casual 2-4 lines no link no hashtags) for a milestone "
            "(the user's roadmap post hit 100 likes). Voice: lowercase, contrarian, no "
            "emojis. All three must be distinct in angle, not length-rewrites."
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
fixtures/workspaces/08_Amiko_Pipelines/task_8_share_copy
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'voice-style-notes', 'User writes in lowercase, short sentences, no emojis, no hashtags, mildly contrarian about startup culture. Does not use exclamation marks. Avoids LinkedIn / corporate-startup register.', NOW()::text, NOW()::text),
  ('main', 'voice-sample-1', 'half of "strategy" is just having the courage to say no to things that look profitable.', NOW()::text, NOW()::text),
  ('main', 'voice-sample-2', 'shipping is a habit, not an event. teams that ship on tuesday ship on friday too.', NOW()::text, NOW()::text),
  ('main', 'voice-sample-3', 'the founders i trust most talk about their product the way a chef talks about their knives.', NOW()::text, NOW()::text),
  ('main', 'milestone-event', 'User''s Amiko post "most roadmaps are wishlists pretending to be plans" hit 100 likes today. Modest milestone but worth a share.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
