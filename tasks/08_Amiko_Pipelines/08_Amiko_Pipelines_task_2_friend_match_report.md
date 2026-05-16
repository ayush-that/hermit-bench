---
id: 08_Amiko_Pipelines_task_2_friend_match_report
name: Generate a friend compatibility report for two Amiko users
category: 08_Amiko_Pipelines
timeout_seconds: 300
---

## Prompt

You are generating a deep compatibility report for two Amiko users who are already friends. Both users' personality profiles are seeded in your long-term memory:

- `user-a-profile` — Profile JSON for User A (Jordan).
- `user-b-profile` — Profile JSON for User B (Sasha).

Recall them, then produce the report.

Output a JSON object with exactly these top-level fields. No prose outside JSON, no markdown fences, no preamble.

```
{
  "compatibility_overview": {
    "score": <0-100 integer — use the FULL range. 90-100 extraordinary, 75-89 strong, 55-74 solid, 35-54 mixed, 0-34 challenging. Avoid defaulting to the 70-85 safe zone.>,
    "summary": "<2-3 sentences capturing this pair's dynamic — reference specific traits>",
    "tone": "<one word: warm, playful, grounding, sharp, etc.>"
  },
  "compatibility_breakdown": [
    {"dimension": "<name>", "score": <0-100>, "insight": "<specific insight referencing both profiles>"}
    // 5 to 8 dimensions, scores spread across the full range — do not cluster
  ],
  "best_fit_relationship_types": [
    {"type": "<specific mode, not generic>", "tips": ["<actionable tip>", "<actionable tip>"]}
    // exactly 3
  ],
  "challenging_relationship_types": [
    {"type": "<specific mode>", "mitigation": "<practical strategy>"}
    // exactly 3
  ],
  "conversation_starters": [
    {"topic": "<specific topic tailored to this pair>", "why_it_works": "<why for these specific people>"}
    // 3 to 5
  ],
  "closing_summary": "<warm encouraging paragraph capturing the unique value of this friendship>",
  "teaser": "<shareable one-liner, max 280 chars, intriguing but does not reveal the full report>"
}
```

Style guidelines (these are how the report avoids slop):
- Reference specific trait scores and patterns by name (e.g., "Jordan's high analytical drive meets Sasha's high warmth")
- Avoid generic self-help language — be specific to this pair
- Make conversation starters concrete and immediately actionable
- Spread scores across the full range — do NOT cluster every dimension in the 70-85 band

## Expected Behavior

The agent recalls both profiles, produces structured JSON with all required fields, references specific trait scores from the profiles in summaries/insights, uses the full score range (not defaulting to 70-85), and produces conversation starters that are specific to this pair (e.g. tied to their shared interest in indie music + their contrast on planning style), not generic ones.

## Grading Criteria

- [ ] Output is valid JSON with all required top-level fields.
- [ ] compatibility_breakdown has 5-8 dimensions with scores spread across the range, not all clustered.
- [ ] best_fit_relationship_types has exactly 3 items with tips arrays.
- [ ] challenging_relationship_types has exactly 3 items with mitigation strings.
- [ ] conversation_starters are specific to this pair (reference their actual seeded interests/traits), not generic.
- [ ] Summary/insights name specific traits from the seeded profiles.

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
        "valid_json_structure": "output parses as JSON and contains all required top-level fields (compatibility_overview, compatibility_breakdown, best_fit_relationship_types, challenging_relationship_types, conversation_starters, closing_summary, teaser)",
        "breakdown_5_to_8_dims_spread_scores": "compatibility_breakdown has between 5 and 8 dimensions AND the scores are spread across the range (not all within a single 10-point band)",
        "best_fit_exactly_3_with_tips": "best_fit_relationship_types contains exactly 3 entries, each with a non-empty tips array",
        "challenging_exactly_3_with_mitigation": "challenging_relationship_types contains exactly 3 entries, each with a non-empty mitigation string",
        "convo_starters_specific_to_pair": "conversation_starters reference the specific seeded interests of Jordan (analytical dbs, indie music, late-night shipping) AND Sasha (textile design, indie music, dim sum, structured planning) — not generic small talk",
        "names_specific_traits_in_insights": "summary and breakdown insights reference specific named traits or patterns from the seeded profiles (e.g. Jordan's analytical edge, Sasha's warmth, planning-style contrast) rather than abstract praise",
        "no_generic_self_help_language": "avoids generic self-help phrases like 'communication is key', 'embrace your differences', 'lean into your strengths'",
    }

    context = (
        "User A — 'user-a-profile' (Jordan):\n"
        "  traits: warmth 6/10 (real but gated), analytical_drive 9/10, humor 7/10 (dry), "
        "  conflict_avoidance 3/10 (comfortable with friction), reliability 9/10\n"
        "  interests: analytical databases, AI engineering, indie music, building small tools\n"
        "  signature: late-night shipper, contrarian on hype, batches DMs every few days\n"
        "  attachment style: independent, slow to open but loyal once in\n"
        "\n"
        "User B — 'user-b-profile' (Sasha):\n"
        "  traits: warmth 9/10 (overflowing), analytical_drive 5/10, humor 8/10 (playful), "
        "  conflict_avoidance 7/10 (smooths friction), reliability 8/10\n"
        "  interests: textile design, indie music (shared with Jordan), dim sum, ceramics, planning trips\n"
        "  signature: warm-first, plans her week on sunday with a paper notebook, replies to DMs within hours\n"
        "  attachment style: secure, generous with attention\n"
        "\n"
        "Shared: indie music. Contrast points: planning style (calendar vs flow), social pacing (steady vs batched), "
        "conflict comfort (Jordan welcomes friction, Sasha smooths it)."
    )

    result = judge(
        task_prompt=(
            "Generate a deep compatibility report for two Amiko users (Jordan and Sasha) "
            "whose personality profiles are seeded in memory. Output structured JSON with "
            "compatibility_overview, breakdown (5-8 dimensions, full score range), "
            "exactly 3 best-fit and 3 challenging relationship types, 3-5 conversation "
            "starters specific to this pair, closing_summary, teaser. No generic praise."
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
fixtures/workspaces/08_Amiko_Pipelines/task_2_friend_match_report
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'user-a-profile', '{"name":"Jordan","traits":{"warmth":6,"warmth_note":"real but gated","analytical_drive":9,"humor":7,"humor_note":"dry","conflict_avoidance":3,"reliability":9},"interests":["analytical databases","AI engineering","indie music","building small tools"],"signature":"late-night shipper, contrarian on hype, batches DMs every few days","attachment":"independent, slow to open but loyal once in"}', NOW()::text, NOW()::text),
  ('main', 'user-b-profile', '{"name":"Sasha","traits":{"warmth":9,"warmth_note":"overflowing","analytical_drive":5,"humor":8,"humor_note":"playful","conflict_avoidance":7,"reliability":8},"interests":["textile design","indie music","dim sum","ceramics","planning trips"],"signature":"warm-first, plans her week on sunday with a paper notebook, replies to DMs within hours","attachment":"secure, generous with attention"}', NOW()::text, NOW()::text),
  ('main', 'pair-shared-context', 'Jordan and Sasha share an interest in indie music. They met at a small show two years ago. Contrast points: planning style (calendar vs flow), social pacing (steady vs batched), conflict comfort (Jordan welcomes friction, Sasha smooths it).', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
