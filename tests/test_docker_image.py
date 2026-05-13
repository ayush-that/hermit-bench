"""Verify the hermitbench-ubuntu docker image builds and contains required CLIs."""
import subprocess


def test_image_builds():
    r = subprocess.run(
        ["docker", "build", "-t", "hermitbench-ubuntu:test", "-f", "docker/Dockerfile", "."],
        cwd="/Users/shydev/Amiko/hermit-bench",
        capture_output=True, text=True, timeout=1800,
    )
    assert r.returncode == 0, r.stderr


def test_image_has_hermit_cli():
    r = subprocess.run(
        ["docker", "run", "--rm", "hermitbench-ubuntu:test", "hermit", "--version"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip(), "hermit --version printed nothing"


def test_image_has_postgres():
    r = subprocess.run(
        ["docker", "run", "--rm", "hermitbench-ubuntu:test", "which", "postgres"],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stderr
    assert "postgres" in r.stdout
