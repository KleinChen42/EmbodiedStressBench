import pandas as pd

from embodied_stressbench.metrics.aggregation import aggregate_oracle_gap


def test_aggregate_oracle_gap_by_task_stressor_level():
    df = pd.DataFrame(
        [
            {"task": "T", "baseline": "oracle_target", "stressor": "none", "level": 0, "success": True},
            {"task": "T", "baseline": "oracle_target", "stressor": "none", "level": 0, "success": True},
            {"task": "T", "baseline": "box_center_depth", "stressor": "none", "level": 0, "success": True},
            {"task": "T", "baseline": "box_center_depth", "stressor": "none", "level": 0, "success": False},
        ]
    )
    gap = aggregate_oracle_gap(df)
    assert len(gap) == 1
    assert gap.iloc[0]["baseline"] == "box_center_depth"
    assert gap.iloc[0]["oracle_gap"] == 0.5
