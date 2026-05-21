from __future__ import annotations

import argparse
import traceback
from itertools import product
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from embodied_stressbench.baselines import get_baseline
from embodied_stressbench.envs.task_registry import make_env
from embodied_stressbench.metrics.failure_taxonomy import classify_failure
from embodied_stressbench.stressors import apply_stressor
from embodied_stressbench.utils.io import append_jsonl, ensure_dir, load_yaml, save_json
from embodied_stressbench.utils.seeds import set_global_seed


def _seeds_from_config(cfg: dict) -> List[int]:
    if "seeds" in cfg:
        return [int(s) for s in cfg["seeds"]]
    if "seed_range" in cfg:
        r = cfg["seed_range"]
        return list(range(int(r["start"]), int(r["stop"])))
    return [0]


def run_closed_loop_episode(
    task: str,
    baseline_name: str,
    seed: int,
    output_dir: str | Path,
    query: str,
    backend: str,
    stressor: str,
    level: int,
) -> Dict[str, Any]:
    set_global_seed(seed)
    env = make_env(task=task, backend=backend, seed=seed)
    try:
        obs = env.reset()
        obs, query_after_stress, stress_info = apply_stressor(obs, query, stressor, level, seed)
        baseline = get_baseline(baseline_name)
        pred = baseline.predict_target(obs, query_after_stress, context={"task": task, "seed": seed})

        execution_offset = None
        if "execution_offset" in stress_info.get("params", {}):
            execution_offset = np.asarray(stress_info["params"]["execution_offset"], dtype=float)

        diagnostic_result = env.execute_pick(pred.target_3d, execution_offset=execution_offset)
        scripted = getattr(env, "execute_scripted_task", None)
        if not callable(scripted):
            task_result = diagnostic_result.__class__(
                False,
                "scripted_executor_unsupported",
                {"reason": "environment_has_no_execute_scripted_task"},
            )
        else:
            task_result = scripted(pred.target_3d, execution_offset=execution_offset)

        target_error_l2 = None
        oracle_target = obs.object_metadata.get("oracle_target_3d")
        if pred.target_3d is not None and oracle_target is not None:
            target_error_l2 = float(np.linalg.norm(pred.target_3d - np.asarray(oracle_target, dtype=float)))

        failure_type = classify_failure(pred.failure_reason, task_result.failure_type)
        result: Dict[str, Any] = {
            "status": "ok",
            "task": task,
            "backend": backend,
            "seed": int(seed),
            "baseline": baseline_name,
            "query_original": query,
            "query_used": query_after_stress,
            "stressor": stressor,
            "level": int(level),
            "stress_info": stress_info,
            "diagnostic_success": bool(diagnostic_result.success),
            "task_success": bool(task_result.success),
            "agreement": bool(diagnostic_result.success) == bool(task_result.success),
            "success": bool(task_result.success),
            "failure_type": failure_type,
            "prediction": pred.to_jsonable(),
            "diagnostic_debug": diagnostic_result.debug_info,
            "closed_loop_debug": task_result.debug_info,
            "target_error_l2": target_error_l2,
            "num_detections": len(obs.detections),
        }
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()

    out_dir = ensure_dir(output_dir)
    filename = f"{task}__{baseline_name}__{stressor}_L{level}__seed{seed}.json"
    save_json(out_dir / filename, result)
    return result


def run_closed_loop_matrix(
    config_path: str | Path,
    output_dir: str | Path,
    shard_index: int | None = None,
    num_shards: int | None = None,
    dry_run: bool = False,
) -> None:
    cfg = load_yaml(config_path)
    out = ensure_dir(output_dir)
    summary_path = out / "summary.jsonl"
    resume_root = out.parent if out.name.startswith("shard_") else out

    tasks = cfg.get("tasks", ["PickCube"])
    baselines = cfg.get("baselines", ["oracle_target"])
    stressors = cfg.get("stressors", ["none"])
    levels = [int(x) for x in cfg.get("levels", [0])]
    seeds = _seeds_from_config(cfg)
    backend = cfg.get("env_backend", "mock")
    default_query = cfg.get("default_query", "pick the red cube")
    task_queries = cfg.get("task_queries", {}) or {}

    combinations = list(product(tasks, baselines, stressors, levels, seeds))
    full_total = len(combinations)
    if (shard_index is None) != (num_shards is None):
        raise ValueError("shard_index and num_shards must be provided together")
    if shard_index is not None and num_shards is not None:
        if num_shards <= 0:
            raise ValueError("num_shards must be positive")
        if shard_index < 0 or shard_index >= num_shards:
            raise ValueError("shard_index must satisfy 0 <= shard_index < num_shards")
        combinations = [combo for idx, combo in enumerate(combinations) if idx % num_shards == shard_index]

    if dry_run:
        print(f"Dry run: config={config_path}")
        print(f"Dry run: output={out}")
        print(f"Dry run: full_total_episodes={full_total}")
        print(f"Dry run: selected_episodes={len(combinations)}")
        return

    snapshot = dict(cfg)
    if shard_index is not None and num_shards is not None:
        snapshot["shard"] = {
            "shard_index": int(shard_index),
            "num_shards": int(num_shards),
            "full_total_episodes": int(full_total),
            "shard_total_episodes": int(len(combinations)),
        }
    save_json(out / "experiment_config_snapshot.json", snapshot)

    existing_result_names = {
        path.name
        for path in resume_root.rglob("*.json")
        if path.name != "experiment_config_snapshot.json"
    }
    total = len(combinations)
    print(f"Running closed-loop sanity matrix: {total} episodes -> {out}")
    for count, (task, baseline, stressor, level, seed) in enumerate(combinations, start=1):
        result_file = out / f"{task}__{baseline}__{stressor}_L{level}__seed{seed}.json"
        if result_file.name in existing_result_names:
            print(f"[{count}/{total}] skip existing {result_file.name}")
            continue
        query = task_queries.get(task, default_query)
        try:
            result = run_closed_loop_episode(task, baseline, seed, out, query, backend, stressor, level)
        except Exception as exc:
            result = {
                "status": "error",
                "task": task,
                "backend": backend,
                "seed": int(seed),
                "baseline": baseline,
                "stressor": stressor,
                "level": int(level),
                "diagnostic_success": False,
                "task_success": False,
                "agreement": True,
                "success": False,
                "failure_type": "runner_exception",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            }
            save_json(result_file, result)
        existing_result_names.add(result_file.name)
        append_jsonl(summary_path, result)
        print(
            f"[{count}/{total}] {task} {baseline} {stressor} L{level} "
            f"seed={seed} diagnostic={result.get('diagnostic_success')} task={result.get('task_success')}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--shard-index", type=int, default=None)
    parser.add_argument("--num-shards", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_closed_loop_matrix(
        args.config,
        args.output,
        shard_index=args.shard_index,
        num_shards=args.num_shards,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
