"""Tests for src/utils/docker_utils.py — exercise the hermit container lifecycle."""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.docker_utils import (  # noqa: E402
    discover_gateway_port,
    read_admin_token,
    remove_container,
    start_container,
    wait_for_gateway,
)


def _docker_available() -> bool:
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker not available on this host"
)


def test_start_and_remove_container() -> None:
    cid = f"hb-test-{uuid.uuid4().hex[:6]}"
    start_container(cid, workspace_host=None, extra_env="")
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True
        )
        assert cid in r.stdout
    finally:
        remove_container(cid)
    r = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True
    )
    assert cid not in r.stdout


def test_wait_for_gateway_and_admin_token_and_port() -> None:
    cid = f"hb-test-{uuid.uuid4().hex[:6]}"
    start_container(cid, workspace_host=None, extra_env="")
    try:
        wait_for_gateway(cid, timeout_seconds=120)
        token = read_admin_token(cid)
        assert token and len(token) >= 32, f"unexpected admin token: {token!r}"
        host, port = discover_gateway_port(cid)
        assert host == "127.0.0.1"
        assert isinstance(port, int) and port > 0
    finally:
        remove_container(cid)
