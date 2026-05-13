"""End-to-end smoke test for the OpenHermitAgent runner.

Hits OpenRouter for real (one cheap call to `openai/gpt-4o-mini`) if
`OPENROUTER_API_KEY` is set in the environment; otherwise the test is
skipped.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.base import AgentTaskSpec  # noqa: E402
from src.agents.openhermit.runner import OpenHermitAgent  # noqa: E402


pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="needs OPENROUTER_API_KEY to drive a real model",
)


def test_runner_executes_one_turn(tmp_path: Path) -> None:
    agent = OpenHermitAgent(openrouter_api_key=os.environ["OPENROUTER_API_KEY"])
    task_id = f"hb-runner-{uuid.uuid4().hex[:6]}"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    spec = AgentTaskSpec(
        task_id=task_id,
        task={"env": "", "warmup": "", "skills": "", "skills_path": ""},
        workspace_path=str(tmp_path),
        prompt="Reply with exactly the string OK and nothing else.",
        timeout_seconds=180,
        output_dir=output_dir,
        model="openai/gpt-4o-mini",
    )
    result = agent.run_task(spec)
    try:
        assert result.error is None, f"runner errored: {result.error}"
        usage = agent.collect_usage(task_id, output_dir, result.elapsed_time)
        (output_dir / "usage.json").write_text(json.dumps(usage, indent=2))
        # The assistant turn should have populated tokens and (small but >0) cost.
        assert usage["request_count"] >= 1, f"no assistant messages recorded: {usage}"
        assert usage["input_tokens"] > 0
        assert usage["output_tokens"] > 0
        # OpenRouter reports cost on every chat completion when the upstream
        # provider supplies pricing. gpt-4o-mini does.
        assert usage["cost_usd"] > 0.0, f"cost not populated: {usage}"
    finally:
        from src.utils.docker_utils import remove_container
        remove_container(task_id)
