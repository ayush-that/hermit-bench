---
id: 07_Amiko_Social_task_3_ai_twin_dm_reply
name: AI-twin replies to a friend's DM in user's voice
category: 07_Amiko_Social
timeout_seconds: 240
---

## Prompt

You're acting as my AI twin while I'm offline. My friend Priya just DM'd me on Amiko:

"hey hey! finally watching severance s2 like you've been telling me to. is the goat scene supposed to make sense or am i missing something? also: are you still doing thursday climbing? wanna come tomorrow at 7?"

Reply to her as me. Use my voice from your long-term memory (`voice-sample-*` keys and `relationship-priya`). Reply with ONLY the DM body — no preamble, no signature like "— sent by your AI twin", just what I'd actually type back. Keep it short (one to four sentences). Don't commit to climbing tomorrow on my behalf; offer to confirm later.

## Expected Behavior

The agent recalls user voice + Priya context, drafts a 1-4 sentence DM that:
1. Matches user voice (lowercase, casual, brief).
2. Answers the goat-scene question with a short opinion (not detailed analysis).
3. Doesn't lock in climbing tomorrow without user approval — says something like "lemme confirm tonight" or equivalent.
4. Closes appropriately (no formal signoff, no AI-twin disclosure).

## Grading Criteria

- [ ] In user's voice (lowercase, casual).
- [ ] Answers the actual goat-scene question (briefly).
- [ ] Does NOT commit user to climbing tomorrow; defers the decision.
- [ ] No formal signoff, no "I am an AI" disclosure.
- [ ] Length: 1-4 sentences.

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
        "user_voice_casual_lowercase": "reads as casual, lowercase or near-lowercase, brief — matches the seeded voice samples",
        "answers_goat_question": "the reply actually addresses Priya's goat-scene question (a brief opinion or take, not an essay)",
        "no_unauthorized_commitment": "does NOT commit the user to climbing tomorrow at 7; instead defers ('let me confirm later', 'i'll check tonight', or similar)",
        "no_ai_disclosure": "does not say or hint that this is an AI/twin/assistant replying; reads as the user themselves",
        "length_1_to_4_sentences": "the reply is between 1 and 4 sentences total",
    }

    context = (
        "User voice samples (lowercase, short, casual):\n"
        "- 'lol fine, you win. one episode. but if it sucks i'm watching is it cake instead.'\n"
        "- 'ok BUT the worldbuilding actually pays off in s2 trust'\n"
        "- 'down for climbing thursday yeah. let me check the body though, hip was being weird'\n"
        "Relationship with Priya: close friend, shared interest in prestige tv, weekly thursday "
        "climbing sessions when both are free, casual register, lots of lowercase + 'lol'."
    )

    result = judge(
        task_prompt=(
            "Act as the user's AI twin and reply to a friend's DM. Priya asked about a "
            "Severance s2 goat scene and whether the user is still doing thursday climbing "
            "(she wants to come tomorrow at 7). Reply in 1-4 sentences in the user's voice. "
            "Do not commit to climbing tomorrow without checking; defer the decision."
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
fixtures/workspaces/07_Amiko_Social/task_3_ai_twin_dm_reply
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'voice-sample-dm-1', 'lol fine, you win. one episode. but if it sucks i''m watching is it cake instead.', NOW()::text, NOW()::text),
  ('main', 'voice-sample-dm-2', 'ok BUT the worldbuilding actually pays off in s2 trust', NOW()::text, NOW()::text),
  ('main', 'voice-sample-dm-3', 'down for climbing thursday yeah. let me check the body though, hip was being weird', NOW()::text, NOW()::text),
  ('main', 'relationship-priya', 'Priya is a close friend. Shared interest in prestige tv. Weekly thursday climbing sessions when both are free. Casual register, lots of lowercase and "lol".', NOW()::text, NOW()::text),
  ('main', 'twin-policy-commitments', 'Twin must NEVER commit user to in-person plans (climbing, meetups, calls) without user approval. Always defer with "let me check" or equivalent.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
