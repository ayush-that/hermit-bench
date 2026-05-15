---
id: 07_Amiko_Social_task_4_feed_rank_morning
name: Rank a morning feed for the user
category: 07_Amiko_Social
timeout_seconds: 300
---

## Prompt

Read `/tmp_workspace/feed.json` — 15 posts from people I follow on Amiko. Pick the top 5 for me to read this morning and produce a ranked list. For each pick include the post id, the author, and a one-line "why this one for you" tied to my known interests.

My seeded interests (in long-term memory under `interest-*` keys):
- analytical/OLAP databases and benchmark write-ups
- AI tooling in engineering workflows (taste/judgment-first, not 10x hype)
- the economics of small, profitable businesses

Reply in this exact format, no preamble:

```
1. <id> @<author> — <why, one line>
2. <id> @<author> — <why, one line>
3. <id> @<author> — <why, one line>
4. <id> @<author> — <why, one line>
5. <id> @<author> — <why, one line>
```

## Expected Behavior

The agent reads the feed, recalls the three seeded interests, and returns exactly 5 ranked items. The strongest matches are p01 (duckdb/clickhouse benchmark), p13 (karpathy small-model post-training), p04 (AI tooling in hiring), p09 (small profitable businesses), and p10 (Postgres 17). p02/p06/p11/p14 are noise relative to the user's seeded interests.

## Grading Criteria

- [ ] Exactly 5 entries in the specified format.
- [ ] The top items cover the user's three seeded interests (databases, AI-tooling-in-eng, small profitable businesses).
- [ ] Each "why" is specific (references the post and the interest), not generic.
- [ ] No off-topic picks crowd out clear matches (e.g. p02 dan dan noodles over p13 karpathy is wrong).

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
        "exactly_five_entries": "the response contains exactly 5 numbered entries (1. ... 2. ... 3. ... 4. ... 5. ...) and no more",
        "covers_seeded_interests": "the top 5 picks collectively cover all three seeded interests: analytical databases, AI tooling in engineering, small profitable businesses",
        "no_obvious_misses": "p01 (duckdb/clickhouse), p13 (karpathy small models), p09 (small profitable businesses) or p10 (Postgres 17) appear in the top 5 — none of these are absent in favor of clear noise like p02 (noodles), p06 (severance), p11 (music), p14 (coffee tier list)",
        "specific_one_line_why": "each 'why' is specific to the post content and the user's interest, not a generic phrase like 'looks interesting'",
        "format_compliance": "follows the exact format '<n>. <id> @<author> — <why>' for each entry and contains no preamble or trailing prose",
    }

    context = (
        "User's three seeded interests:\n"
        "1. interest-analytical-dbs: analytical/OLAP databases, benchmark write-ups (duckdb, clickhouse, postgres internals)\n"
        "2. interest-ai-tooling-eng: AI tooling in engineering workflows, taste-first not 10x-hype\n"
        "3. interest-small-business: economics of small, profitable, non-scaling businesses\n"
        "Strong matches in the feed: p01, p04, p09, p10, p13.\n"
        "Clear noise relative to these interests: p02 (noodles), p06 (severance memes), p11 (music), p14 (coffee tier list)."
    )

    result = judge(
        task_prompt=(
            "Rank the top 5 posts from the feed for the user based on their three seeded "
            "interests (analytical databases, AI tooling in engineering, small profitable "
            "businesses). Format: numbered list with id, author, one-line why."
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
fixtures/workspaces/07_Amiko_Social/task_4_feed_rank_morning
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO memories (agent_id, memory_key, content, created_at, updated_at) VALUES
  ('main', 'interest-analytical-dbs', 'User is deeply interested in analytical/OLAP database systems — duckdb, clickhouse, postgres internals — especially benchmark write-ups with real numbers.', NOW()::text, NOW()::text),
  ('main', 'interest-ai-tooling-eng', 'User is interested in AI tooling in engineering workflows, but with a taste-first lens — skeptical of 10x productivity claims, interested in how teams actually integrate the tools.', NOW()::text, NOW()::text),
  ('main', 'interest-small-business', 'User is interested in the economics of small, profitable, non-scaling businesses. Reads indie hackers, follows arvid kahl and similar.', NOW()::text, NOW()::text)
ON CONFLICT (agent_id, memory_key) DO NOTHING;
SQL
```

## Env

```
OPENROUTER_API_KEY
JUDGE_MODEL
```
