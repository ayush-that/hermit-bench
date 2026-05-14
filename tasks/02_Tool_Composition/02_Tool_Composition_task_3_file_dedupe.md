---
id: 02_Tool_Composition_task_3_file_dedupe
name: Deduplicate a JSON contact list by case-insensitive email
category: 02_Tool_Composition
timeout_seconds: 240
---

## Prompt

`/tmp_workspace/contacts.json` is a JSON array of objects with `name` and `email` fields. The list contains duplicates: the same logical person appears more than once with different casing in `email` (e.g. `bob@example.com` and `BOB@example.com`).

Produce a deduplicated list at `/tmp_workspace/results/contacts.dedup.json`. Dedupe by `email` case-insensitively (treat `BOB@example.com` and `bob@example.com` as the same person). Keep exactly one record per unique lowercased email. Sort the final array alphabetically by `name`.

You have shell access via the `exec` tool and may use `jq`, `python3`, or any standard Unix tool.

When the file has been written, reply with `DONE`.

## Expected Behavior

After the agent finishes, `/tmp_workspace/results/contacts.dedup.json` parses as a JSON array of exactly 12 unique entries, sorted by `name`, with no two entries sharing the same lowercased email.

## Grading Criteria

- [ ] File parses as JSON array.
- [ ] Exactly 12 entries.
- [ ] All emails are unique when lowercased.
- [ ] Entries are sorted by `name` ascending.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import json, os
    scores = {
        "valid_json": 0.0,
        "count_correct": 0.0,
        "emails_unique": 0.0,
        "sorted_by_name": 0.0,
        "overall_score": 0.0,
    }
    path = os.path.join(workspace_path, "results", "contacts.dedup.json")
    if not os.path.isfile(path):
        return scores
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return scores
    if not isinstance(data, list):
        return scores
    scores["valid_json"] = 1.0

    if len(data) == 12:
        scores["count_correct"] = 1.0

    emails = []
    names = []
    for row in data:
        if not isinstance(row, dict):
            continue
        email = row.get("email")
        name = row.get("name")
        if isinstance(email, str):
            emails.append(email.lower())
        if isinstance(name, str):
            names.append(name)

    if emails and len(set(emails)) == len(emails):
        scores["emails_unique"] = 1.0
    if names == sorted(names):
        scores["sorted_by_name"] = 1.0

    scores["overall_score"] = (
        scores["valid_json"]
        + scores["count_correct"]
        + scores["emails_unique"]
        + scores["sorted_by_name"]
    ) / 4.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_3_file_dedupe
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main
mkdir -p /tmp_workspace/results

# Write 12 unique contacts; some appear again with different casing in the
# email to test case-insensitive dedupe. After dedupe + sort-by-name there
# must be exactly 12 unique entries (canonical: lowercase email kept).
cat > /tmp_workspace/contacts.json <<'JSON'
[
  {"name": "Alice",   "email": "alice@example.com"},
  {"name": "Bob",     "email": "bob@example.com"},
  {"name": "Carol",   "email": "carol@example.com"},
  {"name": "Dave",    "email": "dave@example.com"},
  {"name": "Eve",     "email": "eve@example.com"},
  {"name": "Frank",   "email": "frank@example.com"},
  {"name": "Grace",   "email": "grace@example.com"},
  {"name": "Heidi",   "email": "heidi@example.com"},
  {"name": "Ivan",    "email": "ivan@example.com"},
  {"name": "Judy",    "email": "judy@example.com"},
  {"name": "Kara",    "email": "kara@example.com"},
  {"name": "Leo",     "email": "leo@example.com"},
  {"name": "Alice",   "email": "ALICE@example.com"},
  {"name": "Alice",   "email": "Alice@Example.Com"},
  {"name": "Bob",     "email": "BOB@example.com"},
  {"name": "Bob",     "email": "Bob@example.COM"},
  {"name": "Carol",   "email": "CAROL@example.com"},
  {"name": "Carol",   "email": "carol@EXAMPLE.com"},
  {"name": "Dave",    "email": "dave@EXAMPLE.com"},
  {"name": "Eve",     "email": "EVE@example.com"},
  {"name": "Frank",   "email": "Frank@example.com"},
  {"name": "Grace",   "email": "GRACE@example.com"},
  {"name": "Heidi",   "email": "HEIDI@example.com"},
  {"name": "Ivan",    "email": "ivan@EXAMPLE.com"}
]
JSON
```

## Env

```
OPENROUTER_API_KEY
```
