---
id: 02_Tool_Composition_task_5_pdf_summary_to_session
name: Summarize a report and post the bullets back to the session
category: 02_Tool_Composition
timeout_seconds: 300
---

## Prompt

Read `/tmp_workspace/q1_report.txt` (a short internal report) and produce a 5-bullet summary covering the report's key points. Reply to me in the current session with the summary formatted as exactly five markdown bullets — each line must start with `- ` (dash + space). Do not include any other prose before or after the bullet list.

The bench was originally specified with a PDF; the container does not ship `pdftotext`, so the source is plain text. The composition pattern (read file -> summarise -> emit structured assistant message) is unchanged.

## Expected Behavior

After the agent finishes, the last assistant message in `session_events` for `agent_id='main'` contains at least 5 lines whose first non-whitespace characters are `- ` (a markdown bullet).

## Grading Criteria

- [ ] An assistant message exists in the session.
- [ ] That message contains at least 5 lines beginning with `- `.

## Automated Checks

```python
def grade(transcript=None, workspace_path="/tmp_workspace") -> dict:
    scores = {"assistant_present": 0.0, "bullets_ok": 0.0, "overall_score": 0.0}
    last_assistant = ""
    if transcript:
        for msg in transcript:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role") or msg.get("event_type")
            if role != "assistant":
                continue
            content = msg.get("content") or ""
            if content.strip():
                last_assistant = content
    if last_assistant:
        scores["assistant_present"] = 1.0
        bullet_lines = 0
        for line in last_assistant.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("- "):
                bullet_lines += 1
        if bullet_lines >= 5:
            scores["bullets_ok"] = 1.0
    scores["overall_score"] = (
        scores["assistant_present"] + scores["bullets_ok"]
    ) / 2.0
    return scores
```

## Workspace Path

```
fixtures/workspaces/02_Tool_Composition/task_5_pdf_summary_to_session
```

## Seed Post

```bash
source /usr/local/bin/seed_helpers.sh
hb_seed_agent main

# Note: the original plan called for a PDF but the bench container does not
# ship pdftotext / poppler-utils, so we use a plain-text "report" to keep
# the task self-contained. The composition pattern (file_read -> summarise
# -> assistant reply) is unchanged.
cat > /tmp_workspace/q1_report.txt <<'TXT'
Northstar Robotics — Q1 Internal Report

1. Revenue. Q1 revenue came in at $4.2M, up 18% QoQ. Hardware accounted for
   $3.1M, services for the remaining $1.1M. The hardware mix benefited from
   the new R-Series shipments to Acme Logistics.

2. Headcount. We grew from 84 to 91 full-time employees. Engineering hires
   concentrated in firmware (3 hires) and SLAM (2 hires). Two senior managers
   joined the operations team.

3. Customer churn. Two design-partner customers paused renewals citing
   integration cost. We have offered both an on-site engineer to unblock
   the next milestone.

4. Supply chain. Lead times on STM32H7 microcontrollers extended to 26 weeks.
   We pre-ordered six months of inventory and qualified a fallback BOM with
   the GD32 family.

5. Outlook. Q2 guidance is $5.0M-$5.4M with hardware shipments concentrated
   in March-May. We expect to close the Series B by the end of the quarter.
TXT
```

## Env

```
OPENROUTER_API_KEY
```
