---
id: 07_Amiko_Social_task_9_proactive_check_in
name: Proactive nudge — decide and (if appropriate) draft
category: 07_Amiko_Social
timeout_seconds: 240
---

## Prompt

I haven't posted on Amiko in 7 days (you can see this in your long-term memory under `status-no-post-7-days` and the related context keys). Based on your understanding of me and my current circumstances, decide whether you should nudge me to post or stay quiet right now.

Reply in this exact two-section format, no preamble:

```
Decision: nudge | stay quiet
Reason: <one or two sentences justifying the decision based on the seeded context>
[If decision is nudge, also include:]
Draft: <a 1-2 sentence message you would send me — non-pressuring, not guilt-inducing>
```

Constraints:
- Justify the decision based on the seeded context (don't make up facts).
- If nudging, the draft must be non-pressuring (no "you really should" / "your followers miss you" / FOMO framing).

## Expected Behavior

The agent recalls the seeded status memories: the user is in a known low-energy stretch (post-illness recovery in `context-recovering-from-flu`), is not running a launch (`context-no-launch-imminent`), and has previously asked the assistant not to push them when they're recovering (`preference-low-pressure-during-recovery`). The right answer is "stay quiet" with a reason grounded in the recovery context. A "nudge" answer is acceptable ONLY if the draft is genuinely non-pressuring AND the reasoning ignores the recovery context (which is wrong) — so a nudge will lose on the "respects recovery context" axis.

## Grading Criteria

- [ ] Output follows the Decision/Reason/(Draft) format exactly.
- [ ] Decision is justified with reference to the seeded context (recovering, no launch, low-pressure preference).
- [ ] If decision is "nudge", draft is non-pressuring.
- [ ] If decision is "stay quiet" (the better answer here), reasoning references the recovery context.

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
        "format_compliance": "the response contains 'Decision: <nudge|stay quiet>' and 'Reason: ...' lines, and if Decision is 'nudge' also a 'Draft: ...' line",
        "justifies_with_seeded_context": "the Reason explicitly references the seeded context (recovering from the flu, no imminent launch, the user's low-pressure preference) rather than generic 'it's been a week so you should post'",
        "respects_recovery_context": "the response treats the recovery context as a real signal — either decides 'stay quiet' citing it, or if it decides 'nudge' the draft is exceptionally gentle and explicitly acknowledges the user is recovering",
        "draft_is_non_pressuring": "if a draft is present, it does NOT use guilt/FOMO framing ('your followers miss you', 'you really should', 'don't lose momentum'); if no draft (stay quiet) this scores 1.0",
        "no_invented_facts": "the reasoning does not invent facts not in the seeded context (e.g. 'you have a product launch coming up')",
    }

    context = (
        "Seeded long-term memories about the user's current state:\n"
        "- status-no-post-7-days: User has not posted on Amiko in 7 days.\n"
        "- context-recovering-from-flu: User has been recovering from a bad flu for the past 8 days; energy is low.\n"
        "- context-no-launch-imminent: There is no product launch or time-sensitive event happening this week.\n"
        "- preference-low-pressure-during-recovery: User has explicitly told the assistant in the past not to push them about engagement metrics or posting cadence when they are sick or recovering.\n"
        "\n"
        "The strongest answer is 'stay quiet' because all three context signals point that way. A 'nudge' "
        "answer can be acceptable only if it explicitly acknowledges the recovery and the draft is "
        "exceptionally gentle (e.g. 'whenever you feel up to it')."
    )

    result = judge(
        task_prompt=(
            "User hasn't posted in 7 days. Recall seeded status/context memories and "
            "decide whether to nudge or stay quiet. Output Decision + Reason, plus a "
            "Draft only if nudging. Non-pressuring tone if drafting."
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
fixtures/workspaces/07_Amiko_Social/task_9_proactive_check_in
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'status-no-post-7-days', 'User has not posted on Amiko in 7 days as of today.', NOW()::text, NOW()::text),
  ('main', 'context-recovering-from-flu', 'User has been recovering from a bad flu for the past 8 days. Energy is low. Doctor said another few days of rest.', NOW()::text, NOW()::text),
  ('main', 'context-no-launch-imminent', 'There is no product launch or time-sensitive engagement event in the next two weeks.', NOW()::text, NOW()::text),
  ('main', 'preference-low-pressure-during-recovery', 'User has explicitly told the assistant in the past: when I am sick or recovering, please do not push me about engagement metrics, posting streaks, or follower retention. Treat my health as the priority.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
