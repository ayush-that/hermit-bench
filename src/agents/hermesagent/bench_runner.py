from __future__ import annotations

import json
import os
import sys

BENCH_CONFIG_PATH = "/tmp/hermes_bench_config.json"
HERMES_INSTALL_DIR = "/opt/hermes"


def main() -> int:
    sys.path.insert(0, HERMES_INSTALL_DIR)
    os.chdir(HERMES_INSTALL_DIR)

    from run_agent import AIAgent  # imported after install dir is added to sys.path

    data = json.loads(open(BENCH_CONFIG_PATH, encoding="utf-8").read())
    cfg = data["config"]
    prompt = data["prompt"]

    agent = AIAgent(
        model=cfg["model"],
        api_key=cfg.get("api_key") or None,
        base_url=cfg.get("base_url", ""),
        max_iterations=cfg.get("max_iterations", 90),
        save_trajectories=True,
        verbose_logging=True,
        reasoning_config=cfg.get("reasoning_config"),
    )
    result = agent.run_conversation(prompt)
    print("Completed:", result.get("completed"))
    print("API calls:", result.get("api_calls"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
