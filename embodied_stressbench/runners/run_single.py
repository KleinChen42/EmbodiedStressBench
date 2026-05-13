from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np

from embodied_stressbench.baselines import get_baseline
from embodied_stressbench.envs.task_registry import make_env
from embodied_stressbench.metrics.failure_taxonomy import classify_failure
from embodied_stressbench.stressors import apply_stressor
from embodied_stressbench.utils.io import ensure_dir, save_json
from embodied_stressbench.utils.seeds import set_global_seed


def run_episode(
    task: str,
    baseline_name: str,
    seed: int,
    output_dir: str | Path,
    query: str = "pick the red cube",
    backend: str = "mock",
    stressor: str = "none",
    level: int = 0,
) -> Dict[str, Any]:
    start = time.time()
    set_global_seed(seed)
    env = make_env(task=task, backend=backend, seed=seed)
    obs = env.reset()

    obs, query_after_stress, stress_info = apply_stressor(
        obs, query=query, stressor_name=stressor, level=level, seed=seed
    )

    baseline = get_baseline(baseline_name)
    pred = baseline.predict_target(obs, query_after_stress, context={"task": task, "seed": seed})

    execution_offset = None
    if stress_info["name"] == "execution_offset":
        execution_offset = np.asarray(stress_info["params"]["execution_offset"], dtype=float)

    exec_result = env.execute_pick(pred.target_3d, execution_offset=execution_offset)
    failure_type = classify_failure(pred.failure_reason, exec_result.failure_type)
    runtime_sec = time.time() - start

    oracle_target = obs.object_metadata.get("oracle_target_3d")
    target_error_l2 = None
    if pred.target_3d is not None and oracle_target is not None:
        target_error_l2 = float(np.linalg.norm(pred.target_3d - np.asarray(oracle_target, dtype=float)))

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
        "success": bool(exec_result.success),
        "failure_type": failure_type,
        "prediction": pred.to_jsonable(),
        "execution_debug": exec_result.debug_info,
        "target_error_l2": target_error_l2,
        "num_detections": len(obs.detections),
        "runtime_sec": runtime_sec,
    }

    out_dir = ensure_dir(output_dir)
    filename = f"{task}__{baseline_name}__{stressor}_L{level}__seed{seed}.json"
    save_json(out_dir / filename, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--query", default="pick the red cube")
    parser.add_argument("--backend", default="mock")
    parser.add_argument("--stressor", default="none")
    parser.add_argument("--level", type=int, default=0)
    args = parser.parse_args()

    result = run_episode(
        task=args.task,
        baseline_name=args.baseline,
        seed=args.seed,
        output_dir=args.output,
        query=args.query,
        backend=args.backend,
        stressor=args.stressor,
        level=args.level,
    )
    print(result)


if __name__ == "__main__":
    main()
