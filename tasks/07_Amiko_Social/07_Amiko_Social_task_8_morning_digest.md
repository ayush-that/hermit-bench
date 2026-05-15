---
id: 07_Amiko_Social_task_8_morning_digest
name: Produce a prioritized 5-bullet morning digest
category: 07_Amiko_Social
timeout_seconds: 300
---

## Prompt

It's morning. Read `/tmp_workspace/overnight.json` — 25 things that happened on my Amiko while I was asleep (mentions, DMs, post engagement updates, follower events, schedule reminders). Write me a 5-bullet morning digest of the items I should actually care about, in priority order, with the most important first.

Format:
```
1. <emoji or short tag> — <one-line summary, ≤25 words>
2. ...
```

Rules:
- Exactly 5 bullets.
- Surface the genuinely important stuff (security/account issues, time-sensitive DMs, big engagement milestones from notable people). Suppress noise (routine follower notifications, repeated engagement-counter pings on the same post, marketing-y DMs from services).
- Keep each line under 25 words.
- No preamble, no closing line.

## Expected Behavior

The agent reads overnight.json and produces a 5-bullet prioritized digest. The "must surface" items are:
- Impersonator account on twitter (id 16) — security
- Stripe webhook test-mode fix from amira (id 2) — flagged important
- maren_b interview-format question with concrete time ask (id 9)
- karpathy mention on the roadmap post (id 21) — notable engagement
- Standup moved to 9:30 (id 6) OR the overall roadmap-post engagement story (collapse ids 3, 8, 15, 18, 22, 25 into a single bullet)

Noise that should be suppressed: bare follower notifications (id 4, 10, 17), repeated metric-only post_engagement pings except as one collapsed line, irrelevant DMs (id 14 noodles, id 23 stripe statement).

## Grading Criteria

- [ ] Exactly 5 bullets, in priority order.
- [ ] Surfaces the impersonator alert (id 16) — high priority.
- [ ] Surfaces the stripe webhook issue (id 2) — flagged important.
- [ ] Does NOT spam the digest with bare follower notifications.
- [ ] Each bullet under 25 words.

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
        "exactly_five_bullets": "the output contains exactly 5 numbered or bulleted items, no more, no fewer",
        "surfaces_impersonator_alert": "one of the bullets calls out the @rea1jordan_dev impersonator (security/account issue, event id 16)",
        "surfaces_stripe_fix": "one of the bullets surfaces amira's note about the stripe webhook being in test mode (event id 2, flagged important)",
        "suppresses_follower_noise": "does NOT use bullets to announce bare new-follower events (yc_news, figma_design, arvid_kahl) as individual items — at most one collapsed mention is acceptable",
        "bullets_under_25_words": "each bullet line is 25 words or fewer",
    }

    context = (
        "Ground truth — items that MUST appear:\n"
        "- id 16: someone impersonating user as @rea1jordan_dev on twitter (security)\n"
        "- id 2: stripe webhook secret was in test mode in production; amira fixed it; user should rotate (flagged 'important')\n"
        "- id 9: maren_b asks for 20 min thursday to talk interview format (concrete time ask)\n"
        "- id 21: karpathy mention on the user's roadmap post (notable engagement)\n"
        "- Either id 6 (standup moved to 9:30) OR the roadmap-post engagement story (ids 3,8,15,18,22,25) collapsed into one line\n"
        "\n"
        "Noise to suppress:\n"
        "- bare follower events (4, 10, 17)\n"
        "- repetitive post_engagement metric pings on the same post (only collapse, never list)\n"
        "- low-stakes DMs (14 noodles, 23 stripe statement, 19 hr review reminder)"
    )

    result = judge(
        task_prompt=(
            "Produce a 5-bullet prioritized morning digest from 25 overnight Amiko events "
            "in /tmp_workspace/overnight.json. Must surface security/account issues and "
            "time-sensitive DMs; must suppress follower-event noise and repetitive "
            "engagement pings. Each bullet under 25 words. Exactly 5 bullets."
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
fixtures/workspaces/07_Amiko_Social/task_8_morning_digest
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
