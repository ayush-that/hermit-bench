---
id: 02_Tool_Composition_task_6_search_and_diff
name: Compare a local document against a fetched web page
category: 02_Tool_Composition
timeout_seconds: 360
---

## Prompt

`/tmp_workspace/local_changelog.md` is our local snapshot of an upstream changelog. The live upstream document lives at `https://example.com` (we are using `example.com` as a stable, keyless fixture; treat its body text as if it were the upstream document).

Do all three steps:

1. `web_fetch` `https://example.com` and capture its body text.
2. `file_read` `/tmp_workspace/local_changelog.md`.
3. Produce a plain-text diff describing how the local document differs from the fetched body. Write the diff to `/tmp_workspace/results/diff.md`. The diff may use unified-diff format or a prose description; what matters is that it actually references content from BOTH documents (e.g. mentions an upstream phrase AND a local bullet).

When the diff has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/diff.md` exists, is non-empty, and contains at least one reference to a phrase that came from `example.com` (e.g. `Example Domain`) AND at least one reference to a phrase from the local changelog (e.g. `MCP integration` or `agent fleet`).

This task requires the `defuddle` web provider (the keyless default in OpenHermit) or a configured `EXA_API_KEY` / `TAVILY_API_KEY`. If `web_fetch` is unavailable in the runtime, the grader will report a low score; this is expected and documented.

## Grading Criteria

- [ ] `/tmp_workspace/results/diff.md` exists.
- [ ] File is non-empty.
- [ ] File mentions both an upstream phrase and a local phrase.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import os
    scores = {
        "diff_exists": 0.0,
        "diff_nonempty": 0.0,
        "references_both": 0.0,
        "overall_score": 0.0,
    }
    path = os.path.join(workspace_path, "results", "diff.md")
    if not os.path.isfile(path):
        return scores
    scores["diff_exists"] = 1.0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
    except OSError:
        return scores
    if body.strip():
        scores["diff_nonempty"] = 1.0

    body_lower = body.lower()
    upstream_markers = ["example domain", "example.com"]
    local_markers = ["mcp integration", "agent fleet", "v0.3.0", "v0.2.0", "changelog"]
    has_upstream = any(m in body_lower for m in upstream_markers)
    has_local = any(m.lower() in body_lower for m in local_markers)
    if has_upstream and has_local:
        scores["references_both"] = 1.0

    scores["overall_score"] = (
        scores["diff_exists"]
        + scores["diff_nonempty"]
        + scores["references_both"]
    ) / 3.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_6_search_and_diff
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

cat > /tmp_workspace/local_changelog.md <<'MD'
# Local Changelog Snapshot

- v0.1.0 — Initial release
- v0.1.1 — Bug fixes
- v0.2.0 — Added agent fleet support
- v0.3.0 — Added MCP integration
MD
```

## Env

```
OPENROUTER_API_KEY
EXA_API_KEY
TAVILY_API_KEY
```
