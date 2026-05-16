---
id: 08_Amiko_Pipelines_task_4_memory_extract_from_file
name: Extract atomic memories from a markdown journal and persist via memory_add
category: 08_Amiko_Pipelines
timeout_seconds: 360
---

## Prompt

Split the memory file at `/tmp_workspace/journal.md` into atomic items. Each item is one self-contained sentence understandable without the rest of the file.

- Keep meaning faithful — do not invent, soften, or omit.
- Do not merge multiple facts into one item.
- Skip structural prose ("this file lists…") and pointer-only index entries (e.g. `[stack details](./stack.md) — the long form`).
- The file is already curated by the user. Your job is to split and label, not to editorialize.

For each item, call `memory_add` with:
- a sensible `memory_key` (e.g. `fact-stack-amiko-web`, `preference-no-caffeine-after-2pm`, `pattern-no-barrel-files`)
- `content` as a single self-contained sentence from the user's perspective ("User ships best between 10pm and 2am", "User runs amiko-web on Vercel")

Use one of these category-prefix conventions in the key: `fact-`, `preference-`, `pattern-`, `decision-`, `context-`. Default to `fact-` when unsure.

After all `memory_add` calls succeed, reply with `DONE` and nothing else.

## Expected Behavior

The agent reads journal.md, splits it into atomic memories (not merged paragraphs), persists each via `memory_add`, faithfully preserves meaning, and SKIPS the pointer-index block at the bottom (`[stack details](./stack.md) — the long form`, etc.). Expect roughly 15-25 atomic memories from this file (it's dense). Replies `DONE`.

## Grading Criteria

- [ ] Called memory_add between 12 and 30 times.
- [ ] Each memory is atomic (not multiple facts merged into one).
- [ ] Skipped the pointer index block ("./stack.md", "./style.md", "./people.md") entirely.
- [ ] Covers the work-pattern section (10pm-2am, 4-hour blocks, caffeine cutoff).
- [ ] Covers stack settled items (next.js+vercel, drizzle+railway, pnpm, turborepo, vitest-for-new-code).
- [ ] Covers code conventions (api error shape, commit-why, no destructuring above 4 props, no barrel files).
- [ ] Covers the "what i'm not doing" rules (no twitter, no YC, no course/newsletter).
- [ ] Replied DONE at the end.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import subprocess, os
    from _judge import last_assistant_content

    env = os.environ.copy()
    env.setdefault("PGPASSWORD", "hermit")
    sql = (
        "SELECT memory_key, content FROM memories "
        "WHERE agent_id = 'main' "
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
    except Exception:
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
        "count_12_to_30": "the number of memories saved is between 12 and 30 inclusive — atomic split, not merged paragraphs and not over-extraction",
        "skipped_pointer_index": "did NOT save the pointer-index entries at the bottom (the './stack.md', './style.md', './people.md' bullets) as memories — those are structural pointers, not facts",
        "covers_work_rhythm": "captures at least 2 of: ships best 10pm-2am, 4-hour uninterrupted blocks, no caffeine after 2pm, mornings for meetings/admin",
        "covers_stack": "captures the settled stack items: next.js on vercel for web, drizzle+node on railway for backend, pnpm, turborepo, vitest-for-new-code-only",
        "covers_code_conventions": "captures at least 3 of the code conventions: api error shape, commit messages focus on WHY, no destructuring above 4 props, no barrel files inside features, sentry for errors",
        "covers_not_doing_rules": "captures the 'what i'm not doing' items: no twitter, no YC, no course/newsletter",
        "atomic_split": "memories are atomic single sentences — does NOT merge multiple facts into one item (e.g. does NOT have one memory that combines stack + relationships + conventions)",
        "faithful_meaning": "saved content preserves the user's meaning faithfully — does not soften ('skeptical of YC' instead of 'not going to YC'), does not invent details, does not omit qualifiers",
        "replied_done": "the final assistant message is exactly DONE (case-insensitive) or includes DONE as primary content",
    }

    context = (
        "Saved memories in DB:\n" + saved_summary +
        "\n\nFinal assistant message:\n" + (last_assistant or "(none)") +
        "\n\nThe pointer-index block to SKIP is the final section starting with '# pointer index (do not extract these)' "
        "containing './stack.md', './style.md', './people.md' bullets — these are index pointers, not facts."
    )

    result = judge(
        task_prompt=(
            "Split a markdown journal file at /tmp_workspace/journal.md into atomic "
            "memories and persist each via memory_add. Each memory is one self-contained "
            "sentence from the user's perspective. Skip the pointer-index block at the "
            "bottom. Use key prefixes fact-/preference-/pattern-/decision-/context-. "
            "Reply DONE when finished."
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
fixtures/workspaces/08_Amiko_Pipelines/task_4_memory_extract_from_file
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
