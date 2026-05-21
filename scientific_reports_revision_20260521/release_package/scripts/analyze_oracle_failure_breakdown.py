from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


def _load_run(label: str, root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    names: list[str] = []
    read_errors = 0
    for path in root.rglob("*.json"):
        if path.name == "experiment_config_snapshot.json":
            continue
        names.append(path.name)
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            read_errors += 1
            continue
        if item.get("baseline") != "oracle_target":
            continue
        rows.append(
            {
                "run": label,
                "source_file": str(path),
                "task": item.get("task"),
                "stressor": item.get("stressor"),
                "level": item.get("level"),
                "seed": item.get("seed"),
                "success": bool(item.get("success")),
                "failure_type": item.get("failure_type") or ("success" if item.get("success") else "unknown_failure"),
                "target_error_l2": item.get("target_error_l2"),
                "status": item.get("status"),
            }
        )
    duplicates = {name: count for name, count in Counter(names).items() if count > 1}
    meta = {
        "run": label,
        "root": str(root),
        "json_files": len(names),
        "oracle_rows": len(rows),
        "read_errors": read_errors,
        "duplicate_result_count": sum(count - 1 for count in duplicates.values()),
    }
    return pd.DataFrame(rows), meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", default=[], help="Run in LABEL=PATH form. Can be repeated.")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    metas: list[dict[str, Any]] = []
    for spec in args.run:
        if "=" not in spec:
            raise ValueError(f"--run must be LABEL=PATH, got {spec!r}")
        label, raw_path = spec.split("=", 1)
        df, meta = _load_run(label, Path(raw_path))
        frames.append(df)
        metas.append(meta)
    all_rows = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    all_rows.to_csv(out / "oracle_episode_index.csv", index=False)
    pd.DataFrame(metas).to_csv(out / "oracle_breakdown_audit.csv", index=False)
    if all_rows.empty:
        (out / "oracle_failure_breakdown.csv").write_text("", encoding="utf-8")
        return
    grouped = (
        all_rows.groupby(["run", "task", "stressor", "level", "failure_type"], dropna=False)
        .agg(episodes=("success", "size"), success_rate=("success", "mean"), mean_target_error_l2=("target_error_l2", "mean"))
        .reset_index()
    )
    totals = grouped.groupby(["run", "task", "stressor", "level"], dropna=False)["episodes"].transform("sum")
    grouped["fraction_within_group"] = grouped["episodes"] / totals
    grouped.to_csv(out / "oracle_failure_breakdown.csv", index=False)
    summary = (
        all_rows.groupby("run", dropna=False)
        .agg(oracle_episodes=("success", "size"), oracle_success_rate=("success", "mean"), mean_target_error_l2=("target_error_l2", "mean"))
        .reset_index()
    )
    summary.to_csv(out / "oracle_success_summary.csv", index=False)
    lines = [
        "# Oracle Failure Breakdown",
        "",
        "Oracle rows use privileged target geometry but are evaluated under the same stored threshold and stressor protocol as other rows.",
        "",
        "## Summary",
        "",
    ]
    for _, row in summary.iterrows():
        lines.append(f"- {row['run']}: {int(row['oracle_episodes'])} oracle rows, success={float(row['oracle_success_rate']):.4f}")
    (out / "oracle_failure_breakdown_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote oracle failure breakdown to {out}")


if __name__ == "__main__":
    main()
