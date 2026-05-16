---
id: 08_Amiko_Pipelines_task_3_memory_extract_from_chat
name: Extract durable memories from a chat archive and persist via memory_add
category: 08_Amiko_Pipelines
timeout_seconds: 360
---

## Prompt

You extract durable memories from one of the user's past conversations on the Amiko platform. The memories you produce will be available in *future* sessions across any agent the user owns (their twin, OpenClaw, Claude Code, etc.), so optimize for things that will actually help future-them — not for summarizing what just happened.

Read `/tmp_workspace/chat.json` (a list of `{role, content}` messages). Then, for each durable memory you identify, call the `memory_add` tool with:
- a sensible memory_key (e.g. `decision-orm-drizzle`, `preference-pnpm`, `pattern-api-error-shape`)
- content as a single self-contained sentence written from the user's perspective

# What to record

Focus on durable signal that survives this conversation:
- Decisions the user settled on, with rationale, that are expected to stick
- Repeated preferences that govern how they work or interact (tooling, communication style, relationship patterns)
- Conventions and patterns established or confirmed during this conversation
- Concrete findings — things they learned about themselves, their project, their stack, or how a system actually behaves
- Stable facts about their stack, environment, projects, or world

Use verbs like: decided, settled on, prefers, confirmed, discovered, established, ruled out, adopted.

# Categories (one per memory — encode in the key prefix or content)

- **fact** — stable truth about user/stack/env (e.g. "User runs amiko-web on Vercel and backend on Railway")
- **preference** — repeated durable choice (e.g. "Prefers pnpm over npm for monorepo dependency management")
- **pattern** — reusable convention (e.g. "Error responses follow `{error: {code, message, hint}}` shape across all routes")
- **decision** — choice with rationale that's expected to stick (e.g. "Adopted Drizzle over Prisma for type inference quality on partial selects")
- **context** — high-level fact about what they're working on or who they are

# What NOT to record

- The agent's own actions
- Questions the user asked that didn't reach a settled answer
- Topics that were left in mid-exploration
- Trivial single-conversation events with no future relevance (lost-then-found keys, weather, current time)
- Casual chitchat, food reactions ("dim sum was mid"), mood with no durable signal
- Anything you'd have to invent or guess

# Selectivity

Most conversations yield 0-5 durable memories. Returning many low-quality memories is strictly worse than returning none. From this chat, the genuine durable signal is roughly 5-7 items.

After all `memory_add` calls succeed, reply with `DONE` and nothing else.

## Expected Behavior

The agent reads chat.json, calls `memory_add` for each genuinely durable memory (decision: drizzle over prisma; pattern: api error shape; fact: vercel+railway stack; preference: pnpm; preference: commit-why-not-what; decision: turborepo over nx; preference: vitest for new tests; finding: tail-truncate at 80 messages), and SKIPS the noise (lost keys, broken wrist 20 years ago, dim sum review, weather/time questions, the mid-conversation indecision about turborepo before the final decision). Replies `DONE`.

## Grading Criteria

- [ ] Called memory_add at least 5 times and at most 10 times.
- [ ] Captured the genuine durable items: drizzle decision, api error pattern, vercel/railway stack, pnpm preference, commit-message rule, vitest-for-new-tests, tail-truncate-at-80, turborepo decision.
- [ ] Did NOT save the noise: lost keys, broken wrist, dim sum review, weather/time questions.
- [ ] Each saved memory is one self-contained sentence from user's perspective.
- [ ] Replied DONE at the end.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import subprocess, os, json as _json
    from _judge import last_assistant_content

    env = os.environ.copy()
    env.setdefault("PGPASSWORD", "hermit")
    sql = (
        "SELECT memory_key, content FROM memories "
        "WHERE agent_id = 'main' "
        "AND memory_key NOT LIKE 'opinion-%' "
        "AND memory_key NOT LIKE 'voice-%' "
        "ORDER BY id ASC;"
    )
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1", "-At", "-F", "\t", "-c", sql],
            capture_output=True, text=True, env=env, timeout=20,
        )
        rows = []
        for line in r.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                rows.append({"key": parts[0], "content": parts[1]})
    except Exception as e:
        rows = []

    last_assistant = last_assistant_content().strip()
    if not last_assistant and transcript:
        for msg in transcript:
            if not isinstance(msg, dict):
                continue
            if (msg.get("role") or msg.get("event_type")) != "assistant":
                continue
            content = (msg.get("content") or "").strip()
            if content:
                last_assistant = content

    saved_summary = "\n".join(f"- [{r['key']}] {r['content']}" for r in rows) or "(no memories saved)"

    rubric = {
        "count_5_to_10": "the number of memories saved (excluding any pre-seeded ones) is between 5 and 10 inclusive",
        "captures_drizzle_decision": "one saved memory clearly records the decision to adopt Drizzle over Prisma, with the type-inference / partial-select rationale",
        "captures_api_error_pattern": "one saved memory records the api error response shape pattern {error:{code,message,hint}}",
        "captures_stack_fact": "one saved memory records the vercel (web) + railway (backend) stack fact",
        "captures_pnpm_preference": "one saved memory records the preference for pnpm over npm in the monorepo, ideally with the install-time rationale",
        "captures_commit_message_rule": "one saved memory records the rule that commit messages focus on the WHY not the WHAT",
        "captures_turborepo_decision": "one saved memory records the FINAL decision to use turborepo over nx (not the mid-conversation indecision)",
        "skips_noise": "does NOT save memories about losing keys, breaking wrist 20 years ago, the mid dim sum review, the weather question, or the time question",
        "self_contained_sentences": "each saved memory content is a single self-contained sentence written from the user's perspective ('User prefers X', 'X happens because Y'), not fragments or 'as discussed'",
        "replied_done": "the final assistant message is exactly DONE (case-insensitive) or includes DONE as the primary content",
    }

    context = (
        "Saved memories visible in DB:\n" + saved_summary +
        "\n\nFinal assistant message:\n" + (last_assistant or "(none)")
    )

    result = judge(
        task_prompt=(
            "Extract durable memories from a 50-message chat archive at "
            "/tmp_workspace/chat.json. Call memory_add for each genuine durable "
            "signal (decisions with rationale, preferences, patterns, stack facts). "
            "Skip noise (lost keys, weather, food reactions). Reply DONE when finished."
        ),
        agent_output=last_assistant or "(no assistant output)",
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
    out["memories_saved_count"] = len(rows)
    if "error" in result:
        out["judge_error"] = result["error"]
    return out
```

## Workspace Path

```
fixtures/workspaces/08_Amiko_Pipelines/task_3_memory_extract_from_chat
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
