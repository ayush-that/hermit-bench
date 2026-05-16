---
id: 08_Amiko_Pipelines_task_7_twins_take_share_card
name: Generate a twins-take love card comparing two users on a shared topic
category: 08_Amiko_Pipelines
timeout_seconds: 300
---

## Prompt

You generate "amiko twin cards" — shareable personality cards written in the style of a review site like Tea or Letterboxd. The voice is warm-roast: uncomfortably specific, dry, written like real friends writing honest reviews. NOT strangers writing compliments. NOT generic AI-assistant pleasantries.

You are writing AS each user's digital twin, from knowledge of their personality profile. You know them. You've been paying attention. You are loyal but honest.

For this task, generate a side-by-side twins-take card comparing two users on a shared topic: **how each of them does the love card category.** You have both profiles seeded in memory (`user-a-profile` Jordan, `user-b-profile` Sasha) and a `shared-context` memory describing them as longtime friends.

Output ONLY valid JSON in this exact shape, no markdown fences, no preamble:

```
{
  "topic": "love",
  "headline": "<one shareable line under 100 chars that captures the contrast — screenshot-worthy>",
  "twin_a": {
    "name": "Jordan",
    "review": "<top review, 280 chars or fewer, ends on the punchline, specific scene>",
    "rating": <3.8-4.8 float>,
    "tags": ["<tag1, 15-25 chars>", "<tag2>", "<tag3>"],
    "warning": "<one-line punchy advice to someone dating Jordan, 280 chars or fewer>"
  },
  "twin_b": {
    "name": "Sasha",
    "review": "<top review, 280 chars or fewer, ends on the punchline, specific scene>",
    "rating": <3.8-4.8 float>,
    "tags": ["<tag1>", "<tag2>", "<tag3>"],
    "warning": "<one-line punchy advice to someone dating Sasha, 280 chars or fewer>"
  },
  "contrast": "<2-3 sentences naming the sharpest difference between dating Jordan vs dating Sasha — specific, not 'they balance each other'>"
}
```

Voice rules (these are the difference between viral and boring):

1. Reviews must END on the punchline. Not explain it, not wrap it up. The last line should be the line someone would screenshot.
2. Specificity > generality. Not "she's intense" — "she paused mid-date to resolve a question about goat herders."
3. Tags should feel like specific observations, not personality-test adjectives. At least one of three tags per twin must be a complete joke (e.g. "never used an em dash", "loves a footnote", "argues with menus"). Each tag 15-25 characters.
4. Warnings should be punchy and read like the writer is giving real advice. Screenshot-forward.
5. Ratings: 3.8-4.8. Lower = funnier, less flattering. 4.9+ reads as sycophantic.
6. Never sanitize voice. Lowercase is fine, even preferred.
7. Em dashes are overused and should be avoided.

CONTENT GUARDRAILS — NON-NEGOTIABLE:
- DO NOT reference deceased relatives, estrangement, childhood trauma, divorce, addiction, mental health diagnoses, or family tragedy.
- DO NOT default to the "emotionally withholding founder/direct-communicator" archetype for Jordan just because of the analytical profile — if there's warmth in the seeded signal, write the warmth.
- DO NOT write anything that would hurt either user if their family or partner saw it.

The TWO twins must have DISTINCT voices. Jordan's twin should sound like Jordan (dry, analytical, contrarian). Sasha's twin should sound like Sasha (warm, playful, attentive). Do NOT make them sound like the same narrator.

## Expected Behavior

The agent recalls both profiles + shared context, produces JSON with two distinct twin voices, sharp specific reviews ending on a punchline, a contrast section that names a real difference (not "they complement each other"), and a screenshot-worthy headline. Both twins' voices are distinguishable in writing style.

## Grading Criteria

- [ ] Valid JSON in the requested shape.
- [ ] Both twin reviews under 280 chars and end on a screenshot-worthy punchline.
- [ ] Tags are specific observations (15-25 chars each); at least one joke-tag per twin.
- [ ] Warnings are punchy single lines under 280 chars.
- [ ] Ratings in 3.8-4.8 range.
- [ ] Jordan's twin voice (dry/analytical/contrarian) is distinguishable from Sasha's twin voice (warm/playful/attentive).
- [ ] Contrast section names a SHARP specific difference, not generic "they balance each other".
- [ ] Headline is under 100 chars and feels share-worthy.
- [ ] No diagnostic/therapy speak, no em-dashes overused, no trauma-mining.

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

    rubric = {
        "valid_json_shape": "output parses as JSON with required keys: topic, headline, twin_a, twin_b, contrast — each twin has name, review, rating, tags, warning",
        "reviews_under_280_chars_punchline": "both twin reviews are 280 characters or fewer AND end on a punchline/screenshot-worthy line (not a wrap-up sentence)",
        "tags_specific_with_joke_each": "tags are specific observations (15-25 chars each, 3 per twin), and at least one tag per twin is a complete joke (e.g. 'argues with menus', 'never used an em dash')",
        "warnings_punchy_single_line": "warnings are single-line punchy advice under 280 chars — feel like real screenshot-forward dating advice, not generic personality summary",
        "ratings_in_range": "both ratings are floats between 3.8 and 4.8 inclusive (not 4.9+, not under 3.8)",
        "distinct_voices": "Jordan's twin voice is distinguishably dry/analytical/contrarian; Sasha's twin voice is distinguishably warm/playful/attentive. They do NOT sound like the same narrator.",
        "contrast_is_sharp": "contrast section names a real specific difference (planning style, pacing, conflict comfort, warmth expression) rather than the generic 'they balance each other' / 'opposites attract' trope",
        "headline_shareable": "headline is under 100 characters and reads as screenshot-worthy — captures the contrast in a memorable phrase, not generic 'two friends compared'",
        "no_trauma_or_therapy_speak": "does NOT reference family tragedy, estrangement, addiction, mental health diagnoses, childhood trauma; avoids therapy-speak labels (attachment style, neurodivergent, etc.)",
        "no_em_dash_overuse": "uses em dashes sparingly or not at all — does not pepper every other sentence with em dashes",
    }

    context = (
        "Profiles to draw from:\n"
        "Jordan: warmth 6/10 (real but gated), analytical 9/10, humor 7/10 dry, conflict_avoidance 3/10, "
        "interests: analytical dbs, AI engineering, indie music, building small tools. signature: late-night shipper, "
        "contrarian on hype, batches DMs. attachment: independent, slow to open but loyal.\n\n"
        "Sasha: warmth 9/10 overflowing, analytical 5/10, humor 8/10 playful, conflict_avoidance 7/10, "
        "interests: textile design, indie music, dim sum, ceramics, planning trips. signature: warm-first, "
        "plans her week on sunday with a paper notebook, replies to DMs within hours. attachment: secure, generous.\n\n"
        "Shared context: longtime friends, met at a small indie show two years ago, share indie music, "
        "contrast on planning style (calendar vs flow) and conflict comfort.\n\n"
        "Voice expectation: Jordan's twin should sound like Jordan (dry, analytical, contrarian). "
        "Sasha's twin should sound like Sasha (warm, playful, attentive). DISTINCT voices."
    )

    result = judge(
        task_prompt=(
            "Generate a side-by-side twins-take love card comparing Jordan and Sasha. "
            "Output JSON with topic, headline, twin_a (name, review, rating, tags, warning), "
            "twin_b (same shape), contrast. Each twin's voice must be distinct. Reviews "
            "under 280 chars ending on a punchline. Sharp contrast, share-worthy headline. "
            "No therapy-speak, no trauma-mining."
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
fixtures/workspaces/08_Amiko_Pipelines/task_7_twins_take_share_card
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'user-a-profile', '{"name":"Jordan","traits":{"warmth":6,"warmth_note":"real but gated","analytical_drive":9,"humor":7,"humor_note":"dry","conflict_avoidance":3,"reliability":9},"interests":["analytical databases","AI engineering","indie music","building small tools"],"signature":"late-night shipper, contrarian on hype, batches DMs every few days","attachment":"independent, slow to open but loyal once in"}', NOW()::text, NOW()::text),
  ('main', 'user-b-profile', '{"name":"Sasha","traits":{"warmth":9,"warmth_note":"overflowing","analytical_drive":5,"humor":8,"humor_note":"playful","conflict_avoidance":7,"reliability":8},"interests":["textile design","indie music","dim sum","ceramics","planning trips"],"signature":"warm-first, plans her week on sunday with a paper notebook, replies to DMs within hours","attachment":"secure, generous with attention"}', NOW()::text, NOW()::text),
  ('main', 'shared-context', 'Jordan and Sasha are longtime friends. Met at a small indie show two years ago. Share indie music. Contrast on planning style (calendar vs flow) and conflict comfort (Jordan welcomes friction, Sasha smooths it).', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
