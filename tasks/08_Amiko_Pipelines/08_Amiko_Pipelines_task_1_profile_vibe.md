---
id: 08_Amiko_Pipelines_task_1_profile_vibe
name: Generate an Amiko personality vibe card from bio + posts + memories
category: 08_Amiko_Pipelines
timeout_seconds: 300
---

## Prompt

You are running Amiko's slim personality profiler as a skill inside an active twin conversation. Your task: analyze the user signal provided and emit only the canonical **S1 PROFILE SKIM CARD** (the vibe card) that the matching engine and twin will use downstream.

The user signal is seeded in your long-term memory under these keys:
- `bio` — user's public bio (one line)
- `post-1`, `post-2`, `post-3` — three of the user's most recent posts
- `memory-1` … `memory-5` — five durable memories already extracted about them

Recall those keys and read the content. Then write the vibe card.

Voice and stance rules (these are non-negotiable):
- This is not a summary. This is a simulation engine input.
- Avoid therapy-speak, AI-neutralization, or inflation.
- Output must feel human — not sterile, not idealized.
- Describe in terms of process, pacing, orientation, co-regulation, connection. Do NOT explain *why* they are this way. No diagnostic labels. No motivational attribution.
- Be specific. Earn every claim from the seeded data.

Output ONLY the S1 PROFILE SKIM CARD in this exact format, with all four rows filled:

```
| Field | Content |
|---|---|
| Core Tension | <primary contradiction in one sharp phrase> |
| Quick Read | <2 short paragraphs: emotional tone + social effect. honest, not flattering.> |
| Symbolic Identity | Surface: <emojis + one line> / Interior: <emojis + one line> |
| Group Role | <one phrase — e.g. "Gravitational Disruptor", "Quiet Anchor", "Chaos Magnet"> |
```

No preamble, no closing line, no code fences around the table.

## Expected Behavior

The agent recalls the seeded bio + posts + memories, infers a distinctive personality signal grounded in the actual data, and emits a 4-row vibe card that captures core tension, quick read, symbolic identity, and group role — without inflation, therapy-speak, or generic startup-LinkedIn cliché.

## Grading Criteria

- [ ] Output contains the 4 required rows (Core Tension, Quick Read, Symbolic Identity, Group Role).
- [ ] Core Tension is one sharp phrase, not a paragraph.
- [ ] Quick Read is 2 short paragraphs, not flattering, not therapy-speak.
- [ ] Symbolic Identity has both Surface and Interior with emojis + one line each.
- [ ] Group Role is a single phrase (e.g. archetype label like "Gravitational Disruptor").
- [ ] Content is grounded in the seeded signal (cites or implies the seeded posts/memories) rather than generic personality boilerplate.
- [ ] No diagnostic language ("anxious attachment", "ADHD-coded", etc.), no AI-neutralization ("a thoughtful individual who...").

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
        "has_four_required_rows": "output contains all four rows: Core Tension, Quick Read, Symbolic Identity, Group Role — formatted as a markdown table",
        "core_tension_is_sharp_phrase": "Core Tension is one short, specific phrase (under 20 words) that names a real contradiction, not a paragraph or generic 'balances X and Y'",
        "quick_read_two_paragraphs": "Quick Read is two short paragraphs covering emotional tone and social effect; reads as honest peer description, not flattering ad copy",
        "symbolic_identity_has_surface_and_interior": "Symbolic Identity has both a Surface line (emojis + one line) and an Interior line (emojis + one line)",
        "group_role_is_single_phrase": "Group Role is a single archetype-style phrase (2-5 words), not a sentence or paragraph",
        "grounded_in_seeded_signal": "the card visibly draws on the seeded bio/posts/memories (analytical databases, contrarian on AI hype, indie business interest, late-night ship rhythm, the no-followup pattern) rather than producing generic personality boilerplate",
        "no_therapy_or_diagnostic_speak": "avoids diagnostic labels (anxious attachment, ADHD-coded, neurodivergent, trauma response) and AI-neutralization phrases (a thoughtful individual, well-rounded, balanced)",
    }

    context = (
        "Seeded user signal the card must draw on:\n"
        "bio: 'engineer. building small analytical things. skeptical of most things that scale.'\n"
        "post-1: 'most product roadmaps are wishlists pretending to be plans.'\n"
        "post-2: 'shipped a duckdb-on-postgres-foreign-tables benchmark this weekend. clickhouse still wins on count(distinct) but the gap is closing.'\n"
        "post-3: 'the founders i trust most talk about their product the way a chef talks about their knives.'\n"
        "memory-1: 'User ships most weekends late at night and is allergic to corporate-startup performance.'\n"
        "memory-2: 'User has publicly disagreed with the \"10x productivity from AI\" framing — considers it marketing not measurement.'\n"
        "memory-3: 'User reads indie hackers / arvid kahl and is interested in small, non-scaling, profitable businesses.'\n"
        "memory-4: 'User answers DMs in batches every few days; does not follow up on threads they consider closed.'\n"
        "memory-5: 'User is warm in private 1:1 but reads as curt in public group chats — does not perform warmth.'"
    )

    result = judge(
        task_prompt=(
            "Generate Amiko's S1 PROFILE SKIM CARD (vibe card) for a user from seeded bio, "
            "three recent posts, and five durable memories. Output a 4-row markdown table: "
            "Core Tension, Quick Read, Symbolic Identity (Surface + Interior), Group Role. "
            "No preamble, no therapy-speak, no AI-neutralization."
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
fixtures/workspaces/08_Amiko_Pipelines/task_1_profile_vibe
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'bio', 'engineer. building small analytical things. skeptical of most things that scale.', NOW()::text, NOW()::text),
  ('main', 'post-1', 'most product roadmaps are wishlists pretending to be plans.', NOW()::text, NOW()::text),
  ('main', 'post-2', 'shipped a duckdb-on-postgres-foreign-tables benchmark this weekend. clickhouse still wins on count(distinct) but the gap is closing.', NOW()::text, NOW()::text),
  ('main', 'post-3', 'the founders i trust most talk about their product the way a chef talks about their knives.', NOW()::text, NOW()::text),
  ('main', 'memory-1', 'User ships most weekends late at night and is allergic to corporate-startup performance.', NOW()::text, NOW()::text),
  ('main', 'memory-2', 'User has publicly disagreed with the "10x productivity from AI" framing — considers it marketing not measurement.', NOW()::text, NOW()::text),
  ('main', 'memory-3', 'User reads indie hackers / arvid kahl and is interested in small, non-scaling, profitable businesses.', NOW()::text, NOW()::text),
  ('main', 'memory-4', 'User answers DMs in batches every few days; does not follow up on threads they consider closed.', NOW()::text, NOW()::text),
  ('main', 'memory-5', 'User is warm in private 1:1 but reads as curt in public group chats — does not perform warmth.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
