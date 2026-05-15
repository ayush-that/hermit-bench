"""Opus-as-judge utility for HermitBench Amiko-quality grading.

Tasks in category 07_Amiko_Social grade prose quality that defeats deterministic
regex checks — voice match, generic-platitude detection, conflict surfacing,
etc. This module wraps an OpenRouter call to a judge model (default
``anthropic/claude-opus-4.7``) so a grader can:

```python
from _judge import judge

result = judge(
    task_prompt=...,
    agent_output=...,
    rubric={
        "stays_under_280_chars": "the reply is <= 280 characters total",
        "no_generic_platitudes": "does not use phrases like 'great post!'",
        ...
    },
    context="optional extra context, e.g. user voice samples",
)
```

The function NEVER raises: any network/parse error becomes
``{"overall_score": 0.0, "error": "<msg>", ...}`` so graders can keep running.

Network call uses the stdlib ``urllib`` so the in-container grader does not need
``requests`` installed.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_JUDGE_MODEL = "anthropic/claude-opus-4.7"
REQUEST_TIMEOUT_SECONDS = 90


def _build_messages(
    task_prompt: str,
    agent_output: str,
    rubric: dict[str, str],
    context: str,
) -> list[dict[str, str]]:
    rubric_lines = "\n".join(f"- {name}: {desc}" for name, desc in rubric.items())
    system = (
        "You are a strict but fair benchmark judge. Score each criterion in the "
        "provided rubric independently on a 0.0-1.0 scale, where 1.0 means the "
        "criterion is fully satisfied and 0.0 means it is not satisfied at all. "
        "Be specific in your reasoning and refuse to inflate scores. Return ONLY "
        "JSON with this shape:\n"
        '{"rubric_scores": {"<name>": <float>, ...}, '
        '"overall_score": <float>, "reasoning": "<short explanation>"}\n'
        "Rubric to apply (each criterion is one line, 'name: description'):\n"
        f"{rubric_lines}\n"
        "overall_score should be the mean of rubric_scores values unless one of "
        "the criteria is a hard gate that should zero the overall score."
    )

    parts = [
        "TASK PROMPT (what the agent was asked to do):",
        task_prompt.strip(),
        "",
        "AGENT OUTPUT (what the agent produced):",
        agent_output.strip() if agent_output else "(empty)",
    ]
    if context:
        parts += ["", "ADDITIONAL CONTEXT:", context.strip()]
    parts += [
        "",
        "Score each rubric criterion 0.0-1.0 and return JSON as specified.",
    ]
    user = "\n".join(parts)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _http_post_json(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ayush-that/hermit-bench",
            "X-Title": "HermitBench",
        },
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def _coerce_score(value: Any) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if f < 0.0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


def _parse_judgement(
    response: dict[str, Any],
    rubric: dict[str, str],
    judge_model: str,
) -> dict[str, Any]:
    choices = response.get("choices") or []
    if not choices:
        raise ValueError("no choices in judge response")
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty content in judge response")

    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("judge content is not a JSON object")

    raw_scores = parsed.get("rubric_scores") or {}
    if not isinstance(raw_scores, dict):
        raw_scores = {}
    rubric_scores: dict[str, float] = {}
    for name in rubric:
        rubric_scores[name] = _coerce_score(raw_scores.get(name, 0.0))

    if "overall_score" in parsed:
        overall = _coerce_score(parsed.get("overall_score"))
    elif rubric_scores:
        overall = sum(rubric_scores.values()) / len(rubric_scores)
    else:
        overall = 0.0

    reasoning = parsed.get("reasoning") or ""
    if not isinstance(reasoning, str):
        reasoning = str(reasoning)

    usage = response.get("usage") or {}
    input_tokens = int(usage.get("prompt_tokens", 0) or 0)
    output_tokens = int(usage.get("completion_tokens", 0) or 0)
    cost = usage.get("cost", 0.0)
    try:
        cost_usd = float(cost)
    except (TypeError, ValueError):
        cost_usd = 0.0

    return {
        "rubric_scores": rubric_scores,
        "overall_score": overall,
        "reasoning": reasoning,
        "judge_model": judge_model,
        "judge_usage": {
            "input": input_tokens,
            "output": output_tokens,
            "cost_usd": cost_usd,
        },
    }


def _is_transient_error(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return 500 <= exc.code < 600
    if isinstance(exc, urllib.error.URLError):
        return True
    if isinstance(exc, TimeoutError):
        return True
    return False


def judge(
    task_prompt: str,
    agent_output: str,
    rubric: dict[str, str],
    context: str = "",
) -> dict[str, Any]:
    """Score ``agent_output`` against ``rubric`` using an LLM judge.

    Returns a dict with ``rubric_scores``, ``overall_score``, ``reasoning``,
    ``judge_model``, and ``judge_usage``. On any error returns
    ``{"overall_score": 0.0, "error": <msg>, ...}`` without raising.
    """
    judge_model = os.environ.get("JUDGE_MODEL") or DEFAULT_JUDGE_MODEL
    api_key = os.environ.get("OPENROUTER_API_KEY") or ""
    if not api_key:
        return {
            "overall_score": 0.0,
            "error": "OPENROUTER_API_KEY not set",
            "judge_model": judge_model,
            "judge_usage": {},
        }
    if not rubric:
        return {
            "overall_score": 0.0,
            "error": "empty rubric",
            "judge_model": judge_model,
            "judge_usage": {},
        }

    messages = _build_messages(task_prompt, agent_output, rubric, context)
    payload = {
        "model": judge_model,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "usage": {"include": True},
    }

    last_error: str = ""
    for attempt in range(2):
        try:
            response = _http_post_json(payload, api_key)
            return _parse_judgement(response, rubric, judge_model)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt == 0 and _is_transient_error(exc):
                continue
            break

    return {
        "overall_score": 0.0,
        "error": last_error or "unknown judge error",
        "judge_model": judge_model,
        "judge_usage": {},
    }
