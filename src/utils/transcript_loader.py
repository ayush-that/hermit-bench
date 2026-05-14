"""Transcript loader used by the in-container grader.

The HermitBench runner passes ``postgres://session_events`` as the transcript
path. When the loader sees that scheme it queries the local Postgres directly
to assemble a list of ``{ts, role, content, payload}`` dicts ordered by
``session_events.id``. For backwards compatibility, anything else is treated
as a filesystem path (JSON array or JSONL).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

OPENCLAW_FALLBACK_PATH = "/root/.openclaw/agents/main/sessions/chat.jsonl"


def _safe_json_loads(text: str) -> Any | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def _parse_json_lines(raw: str) -> list[Any]:
    rows: list[Any] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parsed = _safe_json_loads(line)
        if parsed is not None:
            rows.append(parsed)
    return rows


def _read_transcript_file(path: Path) -> list[Any]:
    if not path.exists():
        return []

    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    parsed = _safe_json_loads(raw)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("transcript", "messages", "chat"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
        return [parsed]

    return _parse_json_lines(raw)


def _load_from_postgres(agent_id: str = "main") -> list[dict[str, Any]]:
    """Return all session_events for ``agent_id``, oldest first.

    Each event becomes ``{"ts","role","content","event_type","payload"}``. The
    ``role`` field is derived from ``event_type`` (`user` / `assistant` /
    `tool_call` / etc.) so existing graders that look at ``msg["role"]`` work.
    """
    sql = (
        "SELECT ts, event_type, COALESCE(content, ''), payload::text "
        "FROM session_events "
        "WHERE agent_id='%s' "
        "ORDER BY id;" % agent_id.replace("'", "''")
    )
    env = os.environ.copy()
    env.setdefault("PGPASSWORD", "hermit")
    try:
        r = subprocess.run(
            [
                "psql",
                "-U", "hermit",
                "-d", "hermit",
                "-h", "127.0.0.1",
                "-At", "-F", "\t",
                "-c", sql,
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []

    if r.returncode != 0:
        return []

    rows: list[dict[str, Any]] = []
    for line in r.stdout.splitlines():
        if not line:
            continue
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        ts, event_type, content, payload_raw = parts
        payload = _safe_json_loads(payload_raw) or {}
        rows.append({
            "ts": ts,
            "role": event_type,
            "event_type": event_type,
            "content": content,
            "payload": payload,
        })
    return rows


def load_transcript(path_str: str = "") -> list[Any]:
    if path_str.startswith("postgres://"):
        # Path shape: postgres://session_events[/<agent_id>]
        agent_id = "main"
        _, _, tail = path_str.partition("postgres://")
        parts = tail.split("/")
        if len(parts) >= 2 and parts[1]:
            agent_id = parts[1]
        return _load_from_postgres(agent_id)

    candidates: list[str] = []
    if path_str:
        candidates.append(path_str)
    candidates.append(OPENCLAW_FALLBACK_PATH)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        loaded = _read_transcript_file(Path(candidate))
        if loaded:
            return loaded
    return []
