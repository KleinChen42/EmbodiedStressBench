from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from embodied_stressbench.utils.io import iter_json_files
import json


def load_results(input_dir: str | Path) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for path in iter_json_files(input_dir):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "task" in data and "baseline" in data:
                records.append(data)
        except Exception:
            continue
    return pd.DataFrame(records)


def aggregate_success(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(["task", "baseline", "stressor", "level"], dropna=False)
        .agg(success_rate=("success", "mean"), n=("success", "size"))
        .reset_index()
    )


def aggregate_oracle_gap(df: pd.DataFrame, oracle_baseline: str = "oracle_target") -> pd.DataFrame:
    if df.empty or oracle_baseline not in set(df.get("baseline", [])):
        return pd.DataFrame()
    success = aggregate_success(df)
    if success.empty:
        return pd.DataFrame()
    keys = ["task", "stressor", "level"]
    oracle = success[success["baseline"] == oracle_baseline][keys + ["success_rate"]].rename(
        columns={"success_rate": "oracle_success_rate"}
    )
    non_oracle = success[success["baseline"] != oracle_baseline].copy()
    merged = non_oracle.merge(oracle, on=keys, how="left")
    merged["oracle_gap"] = merged["oracle_success_rate"] - merged["success_rate"]
    return merged


def aggregate_summary(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(group_cols, dropna=False)
        .agg(
            success_rate=("success", "mean"),
            n=("success", "size"),
            mean_error=("target_error_l2", "mean"),
        )
        .reset_index()
    )
