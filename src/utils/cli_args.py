from __future__ import annotations

import argparse


def parse_run_batch_args(default_model: str, default_parallel: int) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run HermitBench tasks against an LLM via OpenRouter.")
    p.add_argument(
        "--category",
        default="all",
        help="Category id (01_CLI_Fluency, 02_Tool_Composition, ...) or 'all'.",
    )
    p.add_argument(
        "--task",
        default=None,
        help="Path to a single task markdown file (overrides --category).",
    )
    p.add_argument(
        "--model",
        default=default_model,
        help="OpenRouter model id, e.g. openai/gpt-4o-mini",
    )
    p.add_argument(
        "--parallel",
        type=int,
        default=default_parallel,
        help="Max concurrent task containers.",
    )
    p.add_argument(
        "--thinking",
        default=None,
        help="Optional thinking-budget hint passed to the agent runtime.",
    )
    return p.parse_args()
