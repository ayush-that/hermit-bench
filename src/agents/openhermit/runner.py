"""OpenHermit runner.

Drives one task end-to-end against the gateway HTTP API:

* boots `hermitbench-ubuntu:v0.1` with port 4000 mapped to a random host port,
* reads the gateway admin token from `/root/.openhermit/admin_token`,
* configures agent `main` to route through OpenRouter for the chosen model,
* opens a session via ``POST /api/agents/main/sessions`` and posts a single
  user turn via ``POST .../sessions/<sid>/messages?wait=true``,
* extracts token usage from `session_events.payload->'usage'` for assistant
  rows in Postgres.

Gateway API shapes:

* ``POST /api/agents/{agentId}/sessions`` — body: ``SessionSpec``
    ``{"sessionId": "<id>", "source": {"kind": "cli", "interactive": false}}``.
  Returns ``{"sessionId": "<id>"}``.
* ``POST /api/agents/{agentId}/sessions/{sessionId}/messages?wait=true`` —
  body: ``SessionMessage`` ``{"text": "..."}``. Returns ``SyncResponse``
  ``{"sessionId", "messageId?", "text", "toolCalls", "error?"}``.
* Auth header: ``Authorization: Bearer <admin_token>`` for all ``/api/agents/*`` routes.
"""
from __future__ import annotations

import io
import json
import logging
import shlex
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from src.agents.base import AgentExecution, AgentTaskSpec, BaseAgent
from src.utils.docker_utils import (
    discover_gateway_port,
    dump_postgres,
    exec_in_container,
    read_admin_token,
    start_container,
    wait_for_gateway,
)

logger = logging.getLogger(__name__)


class OpenHermitAgent(BaseAgent):
    """Backend driving the OpenHermit gateway over HTTP for one task."""

    def __init__(
        self,
        openrouter_api_key: str = "",
        openrouter_base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_base_url = openrouter_base_url
        # Per-instance map of task_id -> session_id. Must NOT be a class-level
        # default; concurrent batch runs would otherwise share state.
        self._session_id_by_task: dict[str, str] = {}

    @property
    def expects_gateway(self) -> bool:
        return True

    @property
    def transcript_container_path(self) -> str:
        # Hermit persists session transcripts in Postgres (`session_events`).
        # We dump them via SQL in `collect_usage`. Returned path is only used
        # for code paths that need a string handle.
        return "postgres://session_events"

    # ------------------------------------------------------------------ public

    def run_task(self, spec: AgentTaskSpec) -> AgentExecution:
        try:
            # Materialise task-supplied seed blocks into the workspace dir so
            # the container's entrypoint picks them up (entrypoint.sh runs
            # /tmp_workspace/seed.sql before the gateway boots, then
            # /tmp_workspace/seed_post.sh after /health responds).
            ws = Path(spec.workspace_path)
            ws.mkdir(parents=True, exist_ok=True)
            seed_sql = (spec.task.get("seed_sql") or "").strip()
            seed_post = (spec.task.get("seed_post") or "").strip()
            if seed_sql:
                (ws / "seed.sql").write_text(seed_sql + "\n", encoding="utf-8")
            else:
                (ws / "seed.sql").unlink(missing_ok=True)
            if seed_post:
                (ws / "seed_post.sh").write_text(seed_post + "\n", encoding="utf-8")
            else:
                (ws / "seed_post.sh").unlink(missing_ok=True)

            start_container(
                spec.task_id,
                workspace_host=spec.workspace_path,
                extra_env=spec.task.get("env", ""),
            )
            wait_for_gateway(spec.task_id, timeout_seconds=180)

            self._configure_agent(spec.task_id, spec.model)

            admin_token = read_admin_token(spec.task_id)
            host, port = discover_gateway_port(spec.task_id)
            base_url = f"http://{host}:{port}"

            session_id = f"cli:{uuid.uuid4().hex[:12]}"
            start = time.perf_counter()
            self._open_session(base_url, admin_token, "main", session_id)
            sync = self._post_message_sync(
                base_url, admin_token, "main", session_id,
                spec.prompt, timeout_ms=spec.timeout_seconds * 1000,
            )
            elapsed = time.perf_counter() - start

            self._session_id_by_task[spec.task_id] = session_id
            out = Path(spec.output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "session.json").write_text(
                json.dumps({"sessionId": session_id, "syncResponse": sync}, indent=2),
                encoding="utf-8",
            )

            try:
                dump_postgres(spec.task_id, out)
            except Exception as exc:  # noqa: BLE001
                logger.warning("[%s] pg_dump failed: %s", spec.task_id, exc)

            error: str | None = None
            if isinstance(sync, dict) and sync.get("error"):
                error = str(sync["error"])
            return AgentExecution(elapsed_time=elapsed, error=error)

        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] runner error: %s", spec.task_id, exc)
            return AgentExecution(
                elapsed_time=float(spec.timeout_seconds),
                error=str(exc),
            )

    def collect_usage(
        self,
        task_id: str,
        output_dir: Path,
        elapsed_time: float,
    ) -> dict[str, Any]:
        """Sum usage across all assistant session_events for this task's session."""
        out = Path(output_dir)
        usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "request_count": 0,
            "elapsed_time": round(elapsed_time, 2),
        }

        session_id = self._session_id_by_task.get(task_id)
        if not session_id:
            # Try to recover from session.json on disk.
            session_file = out / "session.json"
            if session_file.exists():
                try:
                    session_id = json.loads(session_file.read_text()).get("sessionId")
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning("[%s] could not recover session id: %s", task_id, exc)
                    session_id = None
        if not session_id:
            return usage

        # Query session_events for assistant entries; payload->'usage' has the
        # pi-ai usage shape `{input, output, cacheRead, cacheWrite, totalTokens, cost:{...}}`.
        sql = (
            "SELECT payload::text FROM session_events "
            f"WHERE agent_id='main' AND session_id={_pg_quote(session_id)} "
            "AND event_type='assistant' ORDER BY id;"
        )
        r = exec_in_container(
            task_id,
            "PGPASSWORD=hermit psql -U hermit -d hermit -h 127.0.0.1 -At -c "
            + shlex.quote(sql),
            timeout=30,
        )
        if r.returncode != 0:
            logger.warning("[%s] usage query failed: %s", task_id, r.stderr.strip())
            return usage

        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            u = payload.get("usage") or {}
            if not isinstance(u, dict):
                continue
            usage["request_count"] += 1
            usage["input_tokens"] += int(u.get("input") or 0)
            usage["output_tokens"] += int(u.get("output") or 0)
            usage["cache_read_tokens"] += int(u.get("cacheRead") or 0)
            usage["cache_write_tokens"] += int(u.get("cacheWrite") or 0)
            usage["total_tokens"] += int(u.get("totalTokens") or 0)
            cost = u.get("cost") or {}
            if isinstance(cost, dict):
                usage["cost_usd"] += float(cost.get("total") or 0.0)
            elif isinstance(cost, (int, float)):
                usage["cost_usd"] += float(cost)

        usage["cost_usd"] = round(usage["cost_usd"], 6)
        return usage

    def prepare_grading_transcript(self, task_id: str) -> str:
        return self.transcript_container_path

    # ------------------------------------------------------------------ helpers

    def _configure_agent(self, task_id: str, model: str) -> None:
        """Create + enable agent ``main``, set the OpenRouter key + model."""
        cmds = [
            "hermit agents create main || true",
            "hermit agents enable main || true",
        ]
        for cmd in cmds:
            r = exec_in_container(task_id, cmd, timeout=30)
            if r.returncode != 0:
                # `create` is idempotent-ish; only fatal if `enable` fails.
                if "enable" in cmd:
                    raise RuntimeError(f"[{task_id}] {cmd} failed: {r.stderr}")

        # Pass the OpenRouter key via a tar-streamed file on stdin so the secret
        # never appears in `docker inspect <container>` (which records the
        # argv of every `docker exec`). The key is shredded immediately after
        # `hermit config` consumes it.
        self._configure_openrouter(task_id, model)

    def _configure_openrouter(self, task_id: str, model: str) -> None:
        key_bytes = self.openrouter_api_key.encode("utf-8")
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo(name=".openrouter_key")
            info.size = len(key_bytes)
            info.mode = 0o600
            tar.addfile(info, io.BytesIO(key_bytes))
        tar_blob = buf.getvalue()

        # `docker cp - <ctr>:<dir>` extracts a tar stream into <dir>.
        cp = subprocess.run(
            ["docker", "cp", "-", f"{task_id}:/tmp"],
            input=tar_blob,
            capture_output=True,
        )
        if cp.returncode != 0:
            raise RuntimeError(
                f"[{task_id}] docker cp openrouter key failed: "
                f"{cp.stderr.decode('utf-8', 'replace').strip()}"
            )

        model_q = shlex.quote(model)
        # `hermit config secrets set` consumes the key from the file we just
        # streamed in, then we shred it. Errors from each step are checked
        # individually (see #9) but the configure call is bundled here to keep
        # the shred always running.
        script = (
            "set -e; "
            "hermit config --agent main secrets set OPENROUTER_API_KEY "
            '"$(cat /tmp/.openrouter_key)"; '
            f"hermit config --agent main set model.provider openrouter; "
            f"hermit config --agent main set model.model {model_q}"
        )
        try:
            r = subprocess.run(
                ["docker", "exec", "-i", task_id, "sh", "-c", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
        finally:
            subprocess.run(
                ["docker", "exec", task_id, "sh", "-c",
                 "shred -u /tmp/.openrouter_key 2>/dev/null || rm -f /tmp/.openrouter_key"],
                capture_output=True,
            )
        if r.returncode != 0:
            raise RuntimeError(
                f"[{task_id}] hermit config failed (rc={r.returncode}): "
                f"stdout={r.stdout.strip()} stderr={r.stderr.strip()}"
            )

    # -- HTTP ----------------------------------------------------------
    def _open_session(
        self,
        base_url: str,
        admin_token: str,
        agent_id: str,
        session_id: str,
    ) -> str:
        payload = {
            "sessionId": session_id,
            "source": {"kind": "cli", "interactive": False},
        }
        body = self._http_json(
            f"{base_url}/api/agents/{agent_id}/sessions",
            payload,
            admin_token,
            method="POST",
            timeout=30,
        )
        sid = body.get("sessionId") if isinstance(body, dict) else None
        if not sid:
            raise RuntimeError(f"open_session: unexpected response {body!r}")
        return sid

    def _post_message_sync(
        self,
        base_url: str,
        admin_token: str,
        agent_id: str,
        session_id: str,
        text: str,
        timeout_ms: int,
    ) -> dict[str, Any]:
        url = (
            f"{base_url}/api/agents/{agent_id}/sessions/{session_id}/messages"
            f"?wait=true&timeout={int(timeout_ms)}"
        )
        payload = {"text": text}
        # urllib timeout is in seconds; add slack for the gateway-side timeout.
        socket_timeout = max(30, (timeout_ms // 1000) + 30)
        body = self._http_json(
            url,
            payload,
            admin_token,
            method="POST",
            timeout=socket_timeout,
            allow_504=True,
        )
        if not isinstance(body, dict):
            raise RuntimeError(f"post_message: unexpected response {body!r}")
        return body

    def _http_json(
        self,
        url: str,
        payload: dict[str, Any],
        admin_token: str,
        method: str = "POST",
        timeout: int = 30,
        allow_504: bool = False,
    ) -> Any:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {admin_token}")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            if allow_504 and exc.code == 504:
                # /messages?wait=true returns 504 with a SyncResponse body on
                # timeout — surface it to the caller instead of raising.
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"error": f"504 timeout: {raw}"}
            raise RuntimeError(
                f"{method} {url} -> HTTP {exc.code}: {raw[:512]}"
            ) from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw


def _pg_quote(text: str) -> str:
    """Quote a string literal for safe embedding in an `psql -c` command."""
    return "'" + text.replace("'", "''") + "'"
