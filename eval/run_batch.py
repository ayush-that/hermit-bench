"""HermitBench batch driver — single backend (OpenHermit), routed via OpenRouter."""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.base import AgentTaskSpec  # noqa: E402
from src.agents.openhermit import OpenHermitAgent  # noqa: E402
from src.utils.cli_args import parse_run_batch_args  # noqa: E402
from src.utils.docker_utils import (  # noqa: E402
    close_proc_log,
    collect_output_from_container,
    remove_container,
)
from src.utils.grading import (  # noqa: E402
    format_scores,
    print_global_summary,
    print_summary,
    run_grading,
    write_error_score,
)
from src.utils.task_parser import parse_task_md  # noqa: E402


load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


ROOT_DIR = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT_DIR / "tasks"
OUTPUT_DIR = ROOT_DIR / "output"

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "openai/gpt-4o-mini")
DEFAULT_PARALLEL = int(os.environ.get("DEFAULT_PARALLEL", "2"))
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

ALL_CATEGORIES = [
    "01_CLI_Fluency",
    "02_Tool_Composition",
    "03_Access_Control",
    "04_Channel_Routing",
    "05_Memory_Introspection",
    "06_Scheduling_Automation",
]


def run_single_task(
    task: dict,
    model: str,
    backend: OpenHermitAgent,
    output_root: Path,
) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_id = uuid.uuid4().hex[:6]
    short_model = re.sub(r"[^a-zA-Z0-9.\-_]", "_", model.rsplit("/", 1)[-1])
    task_id_ori = task["task_id"]
    m = re.match(r"(\d+)_.*?(task_\d+)", task_id_ori)
    short_task_id = f"{m.group(1)}_{m.group(2)}" if m else task_id_ori
    suffix = f"{short_model}_{timestamp}_{run_id}"
    task_id = f"{short_task_id}_{suffix}"
    output_dir = output_root / task["category"] / task_id_ori / suffix
    output_dir.mkdir(parents=True, exist_ok=True)

    result: dict = {"task_id": task_id, "scores": {}, "error": None}
    elapsed = float(task["timeout_seconds"])
    agent_proc = None
    try:
        spec = AgentTaskSpec(
            task_id=task_id,
            task=task,
            workspace_path=task["workspace_path"],
            prompt=task["prompt"],
            timeout_seconds=task["timeout_seconds"],
            output_dir=output_dir,
            model=model,
        )
        execution = backend.run_task(spec)
        agent_proc = execution.agent_proc
        elapsed = execution.elapsed_time
        if execution.error:
            result["error"] = execution.error
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        logger.error("[%s] backend error: %s", task_id, exc)
    finally:
        if task.get("automated_checks"):
            try:
                transcript_path = backend.prepare_grading_transcript(task_id)
                scores = run_grading(
                    task_id=task_id,
                    automated_checks=task["automated_checks"],
                    output_dir=output_dir,
                    extra_env=task.get("env", ""),
                    transcript_container_path=transcript_path,
                    write_error_score=bool(result["error"]),
                )
                result["scores"] = scores
                print(format_scores(task_id, scores))
            except Exception as exc:  # noqa: BLE001
                logger.error("[%s] grading failed: %s", task_id, exc)
                result["scores"] = write_error_score(output_dir, task_id, str(exc))
        usage = backend.collect_usage(
            task_id=task_id, output_dir=output_dir, elapsed_time=elapsed
        )
        result["usage"] = usage
        (output_dir / "usage.json").write_text(
            json.dumps(usage, indent=2), encoding="utf-8"
        )
        try:
            collect_output_from_container(
                task_id, output_dir, include_workspace_changes=True
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] collect_output failed: %s", task_id, exc)
        if agent_proc is not None:
            close_proc_log(agent_proc)
        remove_container(task_id)
    return result


def main() -> None:
    args = parse_run_batch_args(
        default_model=DEFAULT_MODEL, default_parallel=DEFAULT_PARALLEL
    )
    backend = OpenHermitAgent(openrouter_api_key=OPENROUTER_API_KEY)
    output_root = OUTPUT_DIR
    safe_model = re.sub(r"[^a-zA-Z0-9.\-_]", "_", args.model)

    if args.task:
        task = parse_task_md(Path(args.task))
        run_single_task(task, args.model, backend, output_root)
        return

    categories = ALL_CATEGORIES if args.category.lower() == "all" else [args.category]
    all_results: list[dict] = []

    for category in categories:
        category_dir = TASKS_DIR / category
        if not category_dir.exists():
            logger.warning("category dir missing: %s", category_dir)
            continue
        task_files = sorted(category_dir.glob("*task_*.md"))
        tasks: list[dict] = []
        for tf in task_files:
            try:
                tasks.append(parse_task_md(tf))
            except Exception as exc:  # noqa: BLE001
                logger.error("parse %s: %s", tf, exc)

        results: list[dict] = []
        if args.parallel <= 1:
            for t in tasks:
                results.append(run_single_task(t, args.model, backend, output_root))
        else:
            with ThreadPoolExecutor(max_workers=args.parallel) as pool:
                futures = {
                    pool.submit(run_single_task, t, args.model, backend, output_root): t[
                        "task_id"
                    ]
                    for t in tasks
                }
                for f in as_completed(futures):
                    try:
                        results.append(f.result())
                    except Exception as exc:  # noqa: BLE001
                        tid = futures[f]
                        results.append(
                            {"task_id": tid, "scores": {}, "error": str(exc)}
                        )
        print_summary(results, category, output_root, safe_model)
        all_results.extend(results)

    if len(categories) > 1 and all_results:
        print_global_summary(all_results, output_root, safe_model)


if __name__ == "__main__":
    main()
