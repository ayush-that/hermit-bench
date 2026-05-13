#!/usr/bin/env bash
# hermit-bench/script/prepare.sh — build the HermitBench docker image.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[prepare] building hermitbench-ubuntu:v0.1"
docker build -t hermitbench-ubuntu:v0.1 -f docker/Dockerfile .

echo "[prepare] image ready. Set OPENROUTER_API_KEY in .env, then run script/run.sh."
