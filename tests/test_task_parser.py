"""Tests for src.utils.task_parser.parse_task_md."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.task_parser import parse_task_md  # noqa: E402


SAMPLE = """---
id: 01_CLI_Fluency_task_1_smoke
name: Smoke
category: 01_CLI_Fluency
timeout_seconds: 60
---

## Prompt

Reply OK.

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/task_1_smoke
```

## Seed SQL

```sql
INSERT INTO agents (agent_id, workspace_dir, created_at, updated_at)
VALUES ('main', '/root/.openhermit/agents/main', NOW(), NOW());
```

## Seed Post

```bash
hermit agents create main
```

## Env

```
OPENROUTER_API_KEY
```
"""


def test_parses_seed_sections(tmp_path: Path) -> None:
    task_file = tmp_path / "01_CLI_Fluency_task_1_smoke.md"
    task_file.write_text(SAMPLE, encoding="utf-8")
    task = parse_task_md(task_file)

    assert "seed_sql" in task, "parse_task_md must surface seed_sql"
    assert "seed_post" in task, "parse_task_md must surface seed_post"

    assert task["seed_sql"].strip().startswith("INSERT INTO agents")
    assert task["seed_post"].strip().startswith("hermit agents create")


def test_seed_sections_default_to_empty(tmp_path: Path) -> None:
    task_file = tmp_path / "no_seed.md"
    task_file.write_text(
        """---
id: no_seed
name: No Seed
category: 01_CLI_Fluency
timeout_seconds: 30
---

## Prompt

Reply OK.

## Workspace Path

```
fixtures/workspaces/01_CLI_Fluency/no_seed
```

## Env

```
OPENROUTER_API_KEY
```
""",
        encoding="utf-8",
    )
    task = parse_task_md(task_file)
    assert task["seed_sql"] == ""
    assert task["seed_post"] == ""


def test_keeps_existing_fields(tmp_path: Path) -> None:
    """Regression: extension must not drop the existing keys."""
    task_file = tmp_path / "regression.md"
    task_file.write_text(SAMPLE, encoding="utf-8")
    task = parse_task_md(task_file)
    for key in (
        "task_id",
        "prompt",
        "workspace_path",
        "automated_checks",
        "env",
        "timeout_seconds",
        "category",
    ):
        assert key in task, f"missing legacy key {key!r}"
