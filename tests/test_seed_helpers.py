"""Verify seed_helpers.sh provisions a hermit agent inside the container.

Plan deviation: `hermit agents list --json` does not exist (the CLI emits a
plain-text table). The verified gateway HTTP API (`GET /api/agents`) returns
JSON with `agentId` fields, so we assert against that instead.
"""
import subprocess
import uuid


def test_seed_helpers_provision_agent():
    name = f"hb-seed-{uuid.uuid4().hex[:6]}"
    try:
        subprocess.run(
            ["docker", "run", "-d", "--name", name,
             "--entrypoint", "/usr/local/bin/entrypoint.sh",
             "hermitbench-ubuntu:test"],
            check=True, capture_output=True, text=True,
        )
        # Wait for gateway readiness via the in-container healthcheck.
        subprocess.run(
            ["docker", "exec", name, "/usr/local/bin/healthcheck.sh"],
            check=True, capture_output=True, text=True, timeout=120,
        )
        # Provision the agent via the helper, then query the admin HTTP API for
        # the canonical agent list (JSON).
        r = subprocess.run(
            ["docker", "exec", name, "bash", "-c",
             "source /etc/profile.d/hermitbench.sh && "
             "source /usr/local/bin/seed_helpers.sh && "
             "hb_seed_agent main >/dev/null && "
             "curl -fsS -H \"Authorization: Bearer $OPENHERMIT_TOKEN\" "
             "http://127.0.0.1:4000/api/agents"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0, r.stderr
        assert '"agentId":"main"' in r.stdout.replace(" ", ""), r.stdout
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
