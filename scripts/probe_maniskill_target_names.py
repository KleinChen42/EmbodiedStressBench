from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from embodied_stressbench.envs.task_registry import make_env


GENERIC_LABELS = {"", "object", "target object", "requested object", "thing", "item", "ycb object"}


def _is_generic(value: Any) -> bool:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    return text in GENERIC_LABELS


def _probe_task_seed(task: str, seed: int) -> dict[str, Any]:
    env = make_env(task=task, backend="maniskill", seed=seed)
    try:
        obs = env.reset()
    finally:
        close = getattr(env, "close", None)
        if callable(close):
            close()
    debug = obs.object_metadata.get("target_name_debug") or {}
    label = obs.object_metadata.get("target_label")
    category = obs.object_metadata.get("target_category")
    label_source = obs.object_metadata.get("target_label_source")
    non_generic_debug = {
        key: value
        for key, value in debug.items()
        if isinstance(value, str) and not _is_generic(value)
    }
    return {
        "task": task,
        "seed": int(seed),
        "target_label": label,
        "target_category": category,
        "target_label_source": label_source,
        "target_label_is_generic": _is_generic(label),
        "target_category_is_generic": _is_generic(category),
        "non_generic_debug_count": len(non_generic_debug),
        "non_generic_debug": non_generic_debug,
        "target_name_debug_json": json.dumps(debug, sort_keys=True),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", default=["PickSingleYCB", "PickClutterYCB"])
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(10)))
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for task in args.tasks:
        for seed in args.seeds:
            try:
                rows.append(_probe_task_seed(task, seed))
            except Exception as exc:
                rows.append(
                    {
                        "task": task,
                        "seed": int(seed),
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    }
                )
    df = pd.DataFrame(rows)
    df.to_csv(out / "target_name_probe.csv", index=False)
    usable = df[(df.get("target_label_is_generic") == False)]  # noqa: E712
    summary = pd.DataFrame(
        [
            {
                "episodes": int(len(df)),
                "errors": int((df.get("status") == "error").sum()) if "status" in df else 0,
                "non_generic_target_label_rows": int((df.get("target_label_is_generic") == False).sum()),  # noqa: E712
                "non_generic_debug_rows": int(
                    (pd.to_numeric(df.get("non_generic_debug_count", 0), errors="coerce").fillna(0) > 0).sum()
                ),
                "true_name_ablation_allowed": bool(len(usable) > 0),
            }
        ]
    )
    summary.to_csv(out / "target_name_probe_summary.csv", index=False)
    lines = [
        "# ManiSkill YCB Target-Name Probe",
        "",
        f"- Rows: {len(df)}",
        f"- Errors: {int(summary['errors'].iloc[0])}",
        f"- Non-generic target-label rows: {int(summary['non_generic_target_label_rows'].iloc[0])}",
        f"- Non-generic debug rows: {int(summary['non_generic_debug_rows'].iloc[0])}",
        f"- True-name ablation allowed: {bool(summary['true_name_ablation_allowed'].iloc[0])}",
        "",
        "Use the true-name query ablation only when non-generic names are visible in target_label. Debug-only fields are audited but are not enough to run the ablation.",
    ]
    (out / "target_name_probe_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote target-name probe to {out}")


if __name__ == "__main__":
    main()
