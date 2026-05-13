#!/usr/bin/env bash
# hermit-bench/docker/healthcheck.sh — block until the gateway /health endpoint responds.
set -euo pipefail
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:4000/health > /dev/null 2>&1; then
    echo "[healthcheck] gateway ready"
    exit 0
  fi
  sleep 1
done
echo "[healthcheck] gateway failed to become ready within 60s" >&2
exit 1
