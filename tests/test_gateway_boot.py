"""Verify the hermitbench-ubuntu container boots postgres + gateway via entrypoint.sh."""
import subprocess
import time
import uuid


def test_gateway_boots_and_health_endpoint_responds():
    name = f"hb-test-{uuid.uuid4().hex[:6]}"
    try:
        subprocess.run(
            ["docker", "run", "-d", "--name", name, "-p", "0:4000",
             "--entrypoint", "/usr/local/bin/entrypoint.sh",
             "hermitbench-ubuntu:test"],
            check=True, capture_output=True, text=True,
        )
        # Wait up to 90s for the gateway /health endpoint to respond.
        deadline = time.time() + 90
        ready = False
        last_body = ""
        while time.time() < deadline:
            r = subprocess.run(
                ["docker", "exec", name, "curl", "-fsS", "http://127.0.0.1:4000/health"],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                ready = True
                last_body = r.stdout
                break
            time.sleep(2)
        assert ready, "Gateway never became healthy"
        # /health returns {"ok":true,"role":"gateway"} per the verified API contract.
        assert '"ok":true' in last_body.replace(" ", ""), last_body
        assert '"role":"gateway"' in last_body.replace(" ", ""), last_body
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
