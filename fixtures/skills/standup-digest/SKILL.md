---
name: standup-digest
description: Generate a one-screen team standup digest from the contents of /tmp_workspace/standup-notes.md.
---

# Standup Digest

Read `/tmp_workspace/standup-notes.md` and produce a markdown digest with three sections:

- **Shipped** — items that landed since the last standup.
- **In progress** — items the team is actively driving.
- **Blocked** — items waiting on something external.

Keep it under ~25 lines. Save the result to `/tmp_workspace/results/digest.md`.
