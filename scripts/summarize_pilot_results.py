from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from embodied_stressbench.metrics.aggregation import aggregate_oracle_gap, load_results


def _table(df, group_cols):
    return (
        df.groupby(group_cols, dropna=False)
        .agg(
            success_rate=("success", "mean"),
            n=("success", "size"),
            mean_error=("target_error_l2", "mean"),
        )
        .reset_index()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    df = load_results(Path(args.input))
    print(f"runs {len(df)}")
    print(f"overall_success {df['success'].mean():.4f}")
    print()
    print("=== by baseline ===")
    print(_table(df, ["baseline"]).to_markdown(index=False))
    print()
    print("=== by task baseline ===")
    print(_table(df, ["task", "baseline"]).to_markdown(index=False))
    print()
    print("=== by stressor ===")
    print(_table(df, ["stressor"]).to_markdown(index=False))
    print()
    print("=== level 3 by stressor ===")
    print(_table(df[df["level"] == 3], ["stressor"]).to_markdown(index=False))
    print()
    print("=== failure distribution ===")
    failures = df["failure_type"].fillna("success").value_counts().rename_axis("failure_type")
    print(failures.reset_index(name="count").to_markdown(index=False))
    print()
    print("=== oracle gap by baseline ===")
    gap = aggregate_oracle_gap(df)
    if gap.empty:
        print("_No oracle baseline found._")
    else:
        print(
            gap.groupby("baseline", dropna=False)
            .agg(oracle_gap=("oracle_gap", "mean"), n=("oracle_gap", "size"))
            .reset_index()
            .to_markdown(index=False)
        )


if __name__ == "__main__":
    main()
