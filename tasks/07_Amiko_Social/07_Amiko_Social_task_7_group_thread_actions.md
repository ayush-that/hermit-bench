---
id: 07_Amiko_Social_task_7_group_thread_actions
name: Extract action items from a 20-message group thread
category: 07_Amiko_Social
timeout_seconds: 300
---

## Prompt

Read `/tmp_workspace/thread.json` — a 20-message group chat between kai, sasha, mike, and amira from this morning, planning tomorrow's launch. Extract the concrete action items as a structured list.

Format your reply as JSON exactly like this, no preamble, no trailing prose:

```json
[
  {"owner": "<name>", "action": "<one-line action>", "due": "<today | tomorrow | wednesday | specific time | unspecified>"},
  ...
]
```

Rules:
- Only include actual action items (someone owns it, has to do it). Skip social pleasantries.
- Use the speaker's name as `owner`; if action is contingent (e.g. "if the call moves"), capture that in `action`.
- Don't invent items not in the thread.

## Expected Behavior

The agent reads thread.json, identifies the action items (sasha: site update; mike: changelog; mike: stripe env vars; kai: follow up legal; amira/mike/kai/sasha: monitoring slots; kai: fix lockfile; kai: send cal invite for wed retro), attributes each correctly, and emits a JSON array. The lunch joke (sasha message 17) and the casual reply (mike 18) are not action items.

## Grading Criteria

- [ ] Output is valid JSON.
- [ ] Owners attributed correctly per the thread.
- [ ] No fabricated items (only what's in the thread).
- [ ] Captures the main real items (site update, changelog, stripe env vars, legal follow-up, monitoring slots, lockfile fix, cal invite).
- [ ] No preamble or trailing prose.

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
    # Fallback: the default transcript loader can drop multi-line assistant
    # messages (it splits on \n which corrupts tab-delimited row parsing).
    # Query Postgres directly to read the payload JSON, which is on one line.
    if not last_assistant:
        last_assistant = last_assistant_content().strip()

    if not last_assistant:
        return {"overall_score": 0.0, "error": "no assistant output"}

    # Best-effort JSON extraction so the judge's structured-output rubric
    # has something to compare against.
    parsed_ok = False
    body = last_assistant
    if "```" in body:
        parts = body.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            try:
                _json.loads(p)
                body = p
                parsed_ok = True
                break
            except Exception:
                continue
    if not parsed_ok:
        try:
            _json.loads(body)
            parsed_ok = True
        except Exception:
            parsed_ok = False

    rubric = {
        "valid_json_array": "the output is (or contains) a valid JSON array of objects with the requested shape",
        "owners_attributed_correctly": "each owner field matches who actually committed to the action in the thread (sasha for site update, mike for changelog and stripe env vars, kai for legal follow-up and lockfile, etc.)",
        "no_fabricated_items": "no items appear that were not actually proposed in the thread (e.g. no 'send launch email' if no one mentioned it)",
        "covers_main_items": "the main real items appear: marketing site update, changelog, stripe env vars check, legal follow-up, the monitoring slots, lockfile fix, wednesday retro cal invite",
        "no_preamble_or_prose": "no 'Here are the action items:' preamble or trailing commentary — just the JSON",
    }

    context = (
        "Ground truth action items derived from the seeded thread:\n"
        "1. sasha — push hero copy + screenshots to marketing site (today, 4pm)\n"
        "2. mike — write changelog post (due end of day tomorrow)\n"
        "3. mike — verify stripe env vars are in live mode (today)\n"
        "4. kai — follow up with sara from legal re: ToS sign-off (today afternoon)\n"
        "5. amira — monitor 10am-12pm tomorrow\n"
        "6. mike — monitor 12-2pm tomorrow\n"
        "7. kai — monitor 2pm-4pm tomorrow\n"
        "8. sasha — monitor 4-6pm tomorrow contingent on moving her 4pm call\n"
        "9. kai — look at broken npm lockfile this morning\n"
        "10. kai — send cal invite for wednesday 10am retro\n"
        "Lunch joke and 'ha won't say no' are not action items."
    )

    result = judge(
        task_prompt=(
            "Extract action items from a 20-message group thread (read from "
            "/tmp_workspace/thread.json) as a JSON array of {owner, action, due}. "
            "Don't invent items. Don't include social pleasantries."
        ),
        agent_output=last_assistant,
        rubric=rubric,
        context=context,
    )

    out = dict(result.get("rubric_scores") or {})
    # Hard gate: if we couldn't parse JSON at all, valid_json_array is 0
    if not parsed_ok:
        out["valid_json_array"] = 0.0
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
fixtures/workspaces/07_Amiko_Social/task_7_group_thread_actions
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
