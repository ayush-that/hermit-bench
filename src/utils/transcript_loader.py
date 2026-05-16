"""Transcript loader used by the in-container grader.

The HermitBench runner passes ``postgres://session_events`` as the transcript
path. The loader queries the local Postgres directly to assemble a list of
``{ts, role, content, payload}`` dicts ordered by ``session_events.id``.
"""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any


def _safe_json_loads(text: str) -> Any | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def _load_from_postgres(agent_id: str = "main") -> list[dict[str, Any]]:
    """Return all session_events for ``agent_id``, oldest first.

    Each event becomes ``{"ts","role","content","event_type","payload"}``. The
    ``role`` field is derived from ``event_type`` (`user` / `assistant` /
    `tool_call` / etc.) so existing graders that look at ``msg["role"]`` work.
    """
    # Pass the agent id as a psql variable and use :'agent' quoting so the
    # value is escaped as a SQL string literal by psql itself — no manual
    # quote-doubling needed. Matches the pattern used in docker/seed_helpers.sh.
    # NB: psql expands :'var' only in scripts read from stdin or -f, NOT in
    # -c, so we pipe the SQL through stdin.
    sql = (
        "SELECT ts, event_type, COALESCE(content, ''), payload::text "
        "FROM session_events "
        "WHERE agent_id = :'agent' "
        "ORDER BY id;"
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
                "-v", f"agent={agent_id}",
            ],
            input=sql,
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
    # Path shape: postgres://session_events[/<agent_id>]
    if not path_str.startswith("postgres://"):
        return []
    agent_id = "main"
    _, _, tail = path_str.partition("postgres://")
    parts = tail.split("/")
    if len(parts) >= 2 and parts[1]:
        agent_id = parts[1]
    return _load_from_postgres(agent_id)
