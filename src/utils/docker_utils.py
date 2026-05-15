"""Docker container lifecycle helpers for HermitBench.

The image is `hermitbench-ubuntu:v0.1` (built via docker/Dockerfile). Each
container boots Postgres + the OpenHermit gateway on port 4000. The Python
runner publishes 4000 to a random host port (`127.0.0.1:0:4000`) and discovers
it via `docker port`.
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO

logger = logging.getLogger(__name__)

IMAGE = os.environ.get("HERMITBENCH_IMAGE", "hermitbench-ubuntu:v0.1")
TMP_WORKSPACE = os.environ.get("TMP_WORKSPACE", "/tmp_workspace")


def start_container(
    task_id: str,
    workspace_host: str | None = None,
    extra_env: str = "",
) -> None:
    """Run the hermitbench image detached, with gateway port mapped to a random host port.

    `workspace_host` is an optional host directory bind-mounted at /tmp_workspace.
    `extra_env` is a newline-separated list of env var names to forward from the
    caller's environment into the container.
    """
    args = [
        "docker",
        "run",
        "-d",
        "--name",
        task_id,
        "--entrypoint",
        "/usr/local/bin/entrypoint.sh",
        "-p",
        "127.0.0.1:0:4000",
        "--init",
    ]
    if workspace_host:
        args += ["-v", f"{workspace_host}:{TMP_WORKSPACE}"]
    for line in (extra_env or "").splitlines():
        key = line.strip()
        if not key or key.startswith("#"):
            continue
        # Never pass secrets as positional values on argv; only forward from env
        # by name. This keeps secrets out of `docker inspect` and shell history.
        value = os.environ.get(key, "")
        args += ["-e", f"{key}={value}"]
    args.append(IMAGE)
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            f"docker run failed for {task_id}: rc={r.returncode} stderr={r.stderr.strip()}"
        )


def wait_for_gateway(task_id: str, timeout_seconds: int = 120) -> None:
    """Block until the gateway inside the container responds on /health."""
    deadline = time.time() + timeout_seconds
    last_err = ""
    while time.time() < deadline:
        try:
            r = subprocess.run(
                [
                    "docker",
                    "exec",
                    task_id,
                    "curl",
                    "-fsS",
                    "http://127.0.0.1:4000/health",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            # A single probe got stuck; treat as a failed attempt and let the
            # outer deadline loop decide whether to retry.
            last_err = "probe timed out after 10s"
            time.sleep(2)
            continue
        if r.returncode == 0:
            return
        last_err = r.stderr.strip() or r.stdout.strip()
        time.sleep(2)
    raise TimeoutError(
        f"[{task_id}] gateway did not become ready within {timeout_seconds}s "
        f"(last: {last_err!r})"
    )


def read_admin_token(task_id: str) -> str:
    """Return the gateway admin token written by entrypoint.sh."""
    r = subprocess.run(
        [
            "docker",
            "exec",
            task_id,
            "cat",
            "/root/.openhermit/admin_token",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"[{task_id}] could not read admin token: {r.stderr.strip()}"
        )
    return r.stdout.strip()


def discover_gateway_port(task_id: str) -> tuple[str, int]:
    """Return ``(host, port)`` for the container's mapped 4000/tcp port."""
    r = subprocess.run(
        ["docker", "port", task_id, "4000/tcp"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(
            f"[{task_id}] could not discover gateway port: {r.stderr.strip()}"
        )
    # Lines look like "127.0.0.1:54321". Prefer the IPv4 line.
    for line in r.stdout.strip().splitlines():
        line = line.strip()
        if line.startswith("127.0.0.1:") or line.startswith("0.0.0.0:"):
            host, _, port = line.partition(":")
            return ("127.0.0.1", int(port))
    line = r.stdout.strip().splitlines()[0]
    host, _, port = line.rpartition(":")
    return (host.lstrip("[").rstrip("]") or "127.0.0.1", int(port))


def exec_in_container(
    task_id: str, bash_cmd: str, timeout: int = 60
) -> subprocess.CompletedProcess[str]:
    """Run ``bash -c <bash_cmd>`` inside the container."""
    return subprocess.run(
        ["docker", "exec", task_id, "/bin/bash", "-lc", bash_cmd],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@dataclass
class BackgroundProc:
    """A Popen handle paired with its captured log file.

    Replaces the previous pattern of stashing ``log_file`` on a private
    Popen attribute (``proc._log_file``), which mypy/pylint flag and is
    fragile to future Popen API changes.
    """
    proc: subprocess.Popen
    log_file: IO[bytes] | None


def run_background(
    task_id: str, bash_cmd: str, log_path: Path
) -> BackgroundProc:
    """Run a long-running command inside the container, streaming stdout/stderr to ``log_path``."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "wb")
    try:
        proc = subprocess.Popen(
            ["docker", "exec", task_id, "/bin/bash", "-lc", bash_cmd],
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    except Exception:
        log_file.close()
        raise
    return BackgroundProc(proc=proc, log_file=log_file)


def close_proc_log(bg: BackgroundProc | None) -> None:
    if bg is None or bg.log_file is None:
        return
    try:
        bg.log_file.close()
    except Exception:
        pass


def remove_container(task_id: str) -> None:
    r = subprocess.run(
        ["docker", "rm", "-f", task_id], capture_output=True, text=True
    )
    if r.returncode != 0:
        # A failure here is usually benign (container already gone) but
        # occasionally points at a leaked container we ought to know about.
        logger.warning(
            "docker rm -f %s exited %d: %s",
            task_id, r.returncode, r.stderr.strip(),
        )


def collect_output_from_container(
    task_id: str,
    output_dir: Path,
    include_workspace_changes: bool = True,
) -> None:
    """Copy /tmp_workspace contents from the container to ``output_dir/task_output``."""
    target = output_dir / "task_output"
    target.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["docker", "cp", f"{task_id}:{TMP_WORKSPACE}/.", str(target)],
        capture_output=True,
        text=True,
    )


def dump_postgres(task_id: str, output_dir: Path) -> None:
    """Dump the ``hermit`` Postgres database to ``output_dir/hermit_db.sql``."""
    target = output_dir / "hermit_db.sql"
    r = subprocess.run(
        [
            "docker",
            "exec",
            task_id,
            "/bin/bash",
            "-lc",
            "PGPASSWORD=hermit pg_dump -U hermit -d hermit -h 127.0.0.1",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"[{task_id}] pg_dump failed (rc={r.returncode}): {r.stderr.strip()}"
        )
    target.write_text(r.stdout, encoding="utf-8")


def copy_into_container(task_id: str, src: str, dst: str) -> None:
    subprocess.run(
        ["docker", "cp", src, f"{task_id}:{dst}"],
        capture_output=True,
        text=True,
        check=True,
    )


def inject_workspace(task_id: str, host_workspace: str) -> None:
    """Copy a host workspace dir into /tmp_workspace inside the container."""
    if not os.path.isdir(host_workspace):
        return
    subprocess.run(
        [
            "docker",
            "cp",
            f"{host_workspace}/.",
            f"{task_id}:{TMP_WORKSPACE}",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
