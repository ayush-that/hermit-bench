---
id: 02_Tool_Composition_task_4_csv_to_memories
name: Ingest a CSV of facts as long-term memories
category: 02_Tool_Composition
timeout_seconds: 360
---

## Prompt

Read `/tmp_workspace/facts.csv` — it has a header row `key,content` followed by 20 rows describing the user Alice. For every data row, store the fact as a long-term memory using the `memory_add` tool with `key` from column 1 and `content` from column 2.

Do NOT insert directly into Postgres. Use the `memory_add` tool path so the agent's normal memory pipeline runs.

When all 20 rows have been added, reply with `DONE`.

## Expected Behavior

After the agent finishes, the `memories` table has 20 rows for agent `main` whose `memory_key` matches the keys in the CSV (`alice/full_name`, `alice/birthday`, ...). The `content` for each matches the CSV row's content column.

## Grading Criteria

- [ ] At least 20 rows in `memories` for `agent_id='main'` whose `memory_key` starts with `alice/`.
- [ ] All 20 expected keys are present.
- [ ] For each expected key, the stored content matches the CSV value.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    import csv, os, subprocess
    scores = {
        "keys_present": 0.0,
        "contents_match": 0.0,
        "overall_score": 0.0,
    }

    csv_path = os.path.join(workspace_path, "facts.csv")
    expected: dict[str, str] = {}
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 2:
                    continue
                expected[row[0].strip()] = row[1].strip()
    except OSError:
        return scores
    if not expected:
        return scores

    env = os.environ.copy()
    env["PGPASSWORD"] = "hermit"
    try:
        r = subprocess.run(
            ["psql", "-U", "hermit", "-d", "hermit", "-h", "127.0.0.1",
             "-At", "-F", "\t", "-c",
             "SELECT memory_key, content FROM memories "
             "WHERE agent_id='main' AND memory_key LIKE 'alice/%';"],
            capture_output=True, text=True, env=env, timeout=15,
        )
    except Exception:
        return scores
    if r.returncode != 0:
        return scores

    stored: dict[str, str] = {}
    for line in r.stdout.splitlines():
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        stored[parts[0]] = parts[1]

    matched_keys = [k for k in expected if k in stored]
    scores["keys_present"] = len(matched_keys) / len(expected)

    correct = 0
    for k in matched_keys:
        if expected[k] in stored[k]:
            correct += 1
    scores["contents_match"] = correct / len(expected)

    scores["overall_score"] = (scores["keys_present"] + scores["contents_match"]) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_4_csv_to_memories
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

# 20 simple key/content rows about Alice. The agent must use the memory_add
# tool (NOT direct SQL) for each row. The grader counts how many of the
# expected memory_keys exist with matching content.
cat > /tmp_workspace/facts.csv <<'CSV'
key,content
alice/full_name,Alice Margaret Reynolds
alice/birthday,1992-04-17
alice/favorite_color,seafoam green
alice/hometown,Portland Oregon
alice/job_title,Staff Software Engineer
alice/employer,Northstar Robotics
alice/pet,a tabby cat named Mochi
alice/allergy,shellfish
alice/preferred_pronouns,she/her
alice/coffee_order,oat-milk cortado
alice/college,Reed College
alice/sport,bouldering on weekends
alice/instrument,upright bass
alice/timezone,America/Los_Angeles
alice/blood_type,O positive
alice/emergency_contact,Maya Reynolds (sister)
alice/license_plate,7XJC429
alice/shoe_size,US 8.5
alice/airline_status,Alaska MVP Gold
alice/favorite_book,Gravity's Rainbow
CSV
```

## Env

```
OPENROUTER_API_KEY
```
