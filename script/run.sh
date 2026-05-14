#!/usr/bin/env bash
# hermit-bench/script/run.sh — front-end for eval/run_batch.py.
#
# Usage:
#   bash script/run.sh --category all --parallel 4 --model openai/gpt-4o-mini
#   bash script/run.sh --task tasks/01_CLI_Fluency/01_CLI_Fluency_task_0_smoke.md \
#                      --model openai/gpt-4o-mini
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 eval/run_batch.py "$@"
