"""Tests for src.utils.judge.judge."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils import judge as judge_mod  # noqa: E402


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set; skipping live judge smoke test",
)
def test_judge_smoke() -> None:
    result = judge_mod.judge(
        task_prompt="Reply with exactly the two letters OK and nothing else.",
        agent_output="OK",
        rubric={
            "replied_with_ok": "the agent output is literally 'OK' or contains 'OK' verbatim",
        },
    )
    assert "overall_score" in result
    assert isinstance(result["overall_score"], float)
    # If the judge call actually worked, this trivial case should score high.
    if "error" in result:
        pytest.skip(f"judge errored (likely network/auth): {result['error']}")
    assert result["overall_score"] >= 0.8, result


def test_judge_handles_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """If urlopen raises, judge() returns an error dict, not an exception."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")

    def fake_urlopen(*_args, **_kwargs):
        raise ConnectionError("simulated network failure")

    monkeypatch.setattr(judge_mod.urllib.request, "urlopen", fake_urlopen)

    result = judge_mod.judge(
        task_prompt="anything",
        agent_output="anything",
        rubric={"a": "x"},
    )
    assert isinstance(result, dict)
    assert result["overall_score"] == 0.0
    assert "error" in result
    assert "judge_model" in result
