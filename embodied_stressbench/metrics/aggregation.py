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
