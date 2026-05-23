from __future__ import annotations

import argparse
import traceback
from itertools import product
from pathlib import Path
from typing import List

from embodied_stressbench.runners.run_single import run_episode
from embodied_stressbench.utils.io import append_jsonl, ensure_dir, load_yaml, save_json


def _seeds_from_config(cfg: dict) -> List[int]:
    if "seeds" in cfg:
        return [int(s) for s in cfg["seeds"]]
    if "seed_range" in cfg:
        r = cfg["seed_range"]
        return list(range(int(r["start"]), int(r["stop"])))
    return [0]


def run_matrix(
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
    if cfg.get("conditions"):
        conditions = [
            (str(item.get("stressor", "none")), int(item.get("level", 0)))
            for item in cfg["conditions"]
        ]
    else:
        conditions = list(product(stressors, levels))
    seeds = _seeds_from_config(cfg)
    backend = cfg.get("env_backend", "mock")
    default_query = cfg.get("default_query", "pick the red cube")
    task_queries = cfg.get("task_queries", {}) or {}
    query_variants = cfg.get("query_variants") or {}
    if query_variants:
        query_items = [(str(key), str(value)) for key, value in query_variants.items()]
    else:
        query_items = [("", "")]

    combinations = [
        (task, baseline, stressor, level, seed, query_item)
        for task, baseline, (stressor, level), seed, query_item in product(
            tasks, baselines, conditions, seeds, query_items
        )
    ]
    full_total = len(combinations)
    if (shard_index is None) != (num_shards is None):
        raise ValueError("shard_index and num_shards must be provided together")
    if shard_index is not None and num_shards is not None:
        if num_shards <= 0:
            raise ValueError("num_shards must be positive")
        if shard_index < 0 or shard_index >= num_shards:
            raise ValueError("shard_index must satisfy 0 <= shard_index < num_shards")
        combinations = [
            combo for idx, combo in enumerate(combinations) if idx % num_shards == shard_index
        ]

    snapshot = dict(cfg)
    if shard_index is not None and num_shards is not None:
        snapshot["shard"] = {
            "shard_index": int(shard_index),
            "num_shards": int(num_shards),
            "full_total_episodes": int(full_total),
            "shard_total_episodes": int(len(combinations)),
        }
    if dry_run:
        print(f"Dry run: config={config_path}")
        print(f"Dry run: output={out}")
        print(f"Dry run: full_total_episodes={full_total}")
        print(f"Dry run: selected_episodes={len(combinations)}")
        if shard_index is not None and num_shards is not None:
            print(f"Dry run: shard={shard_index}/{num_shards}")
        return

    if any("grounding_dino" in str(baseline) for baseline in baselines):
        try:
            from embodied_stressbench.baselines.rgbd_crop import _get_grounding_dino_provider

            provider = _get_grounding_dino_provider()
            if provider is None:
                print("GroundingDINO warmup: unavailable; rows will report no_detection with diagnostic error.")
            else:
                print(f"GroundingDINO warmup: loaded {provider.model_name} on {provider.device}")
        except Exception as exc:
            print(f"GroundingDINO warmup: failed with {type(exc).__name__}: {exc}")

    existing_result_names = {
        path.name
        for path in resume_root.rglob("*.json")
        if path.name != "experiment_config_snapshot.json"
    }
    save_json(out / "experiment_config_snapshot.json", snapshot)
    shard_msg = "" if shard_index is None else f" shard={shard_index}/{num_shards}"
    print(f"Running matrix{shard_msg}: {len(combinations)} episodes -> {out}")

    count = 0
    total = len(combinations)
    for task, baseline, stressor, level, seed, query_item in combinations:
        count += 1
        query_key, query_template = query_item
        query = query_template or task_queries.get(task, default_query)
        query_part = "" if not query_key else f"__q-{query_key}"
        result_file = out / f"{task}__{baseline}__{stressor}_L{level}__seed{seed}{query_part}.json"
        if result_file.name in existing_result_names:
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
                query_variant=query_key or None,
            )
        except Exception as e:
            result = {
                "status": "error",
                "task": task,
                "backend": backend,
                "seed": int(seed),
                "baseline": baseline,
                "query_variant": query_key or None,
                "query_template": query,
                "stressor": stressor,
                "level": int(level),
                "success": False,
                "failure_type": "runner_exception",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            }
            save_json(result_file, result)
        existing_result_names.add(result_file.name)
        append_jsonl(summary_path, result)
        query_msg = "" if not query_key else f" q={query_key}"
        print(f"[{count}/{total}] {task} {baseline} {stressor} L{level} seed={seed}{query_msg} success={result.get('success')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--shard-index", type=int, default=None)
    parser.add_argument("--num-shards", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run_matrix(
        args.config,
        args.output,
        shard_index=args.shard_index,
        num_shards=args.num_shards,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
