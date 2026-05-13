from __future__ import annotations

import argparse
import traceback
from itertools import product
from pathlib import Path
from typing import Iterable, List

from embodied_stressbench.runners.run_single import run_episode
from embodied_stressbench.utils.io import append_jsonl, ensure_dir, load_yaml, save_json


def _seeds_from_config(cfg: dict) -> List[int]:
    if "seeds" in cfg:
        return [int(s) for s in cfg["seeds"]]
    if "seed_range" in cfg:
        r = cfg["seed_range"]
        return list(range(int(r["start"]), int(r["stop"])))
    return [0]


def run_matrix(config_path: str | Path, output_dir: str | Path) -> None:
    cfg = load_yaml(config_path)
    out = ensure_dir(output_dir)
    summary_path = out / "summary.jsonl"

    tasks = cfg.get("tasks", ["PickCube"])
    baselines = cfg.get("baselines", ["oracle_target"])
    stressors = cfg.get("stressors", ["none"])
    levels = [int(x) for x in cfg.get("levels", [0])]
    seeds = _seeds_from_config(cfg)
    backend = cfg.get("env_backend", "mock")
    query = cfg.get("default_query", "pick the red cube")

    total = len(tasks) * len(baselines) * len(stressors) * len(levels) * len(seeds)
    save_json(out / "experiment_config_snapshot.json", cfg)
    print(f"Running matrix: {total} episodes -> {out}")

    count = 0
    for task, baseline, stressor, level, seed in product(tasks, baselines, stressors, levels, seeds):
        count += 1
        result_file = out / f"{task}__{baseline}__{stressor}_L{level}__seed{seed}.json"
        if result_file.exists():
            print(f"[{count}/{total}] skip existing {result_file.name}")
            continue
        try:
            result = run_episode(
                task=task,
                baseline_name=baseline,
                seed=seed,
                output_dir=out,
                query=query,
                backend=backend,
                stressor=stressor,
                level=level,
            )
        except Exception as e:
            result = {
                "status": "error",
                "task": task,
                "backend": backend,
                "seed": int(seed),
                "baseline": baseline,
                "stressor": stressor,
                "level": int(level),
                "success": False,
                "failure_type": "runner_exception",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            }
            save_json(result_file, result)
        append_jsonl(summary_path, result)
        print(f"[{count}/{total}] {task} {baseline} {stressor} L{level} seed={seed} success={result.get('success')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_matrix(args.config, args.output)


if __name__ == "__main__":
    main()
