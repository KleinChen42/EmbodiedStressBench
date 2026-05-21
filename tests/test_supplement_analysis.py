from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_ieee_access_supplement_analysis import _load_records, grounding_dino_iou_analysis


def test_grounding_dino_iou_analysis_handles_missing_and_low_iou():
    base = Path("ieee_access_revision_20260520/test_tmp_supplement_analysis")
    root = base / "run"
    root.mkdir(parents=True, exist_ok=True)
    (root / "a.json").write_text(
        json.dumps(
            {
                "task": "PickCube",
                "baseline": "crop_median_depth_grounding_dino",
                "stressor": "partial_target_occlusion",
                "level": 3,
                "seed": 0,
                "success": True,
                "target_error_l2": 0.03,
                "failure_type": None,
                "prediction": {"debug_info": {"grounding_dino_target_iou": 0.12}},
            }
        ),
        encoding="utf-8",
    )
    (root / "b.json").write_text(
        json.dumps(
            {
                "task": "PickCube",
                "baseline": "box_center_depth_grounding_dino",
                "stressor": "partial_target_occlusion",
                "level": 3,
                "seed": 1,
                "success": False,
                "target_error_l2": 0.20,
                "failure_type": "target_error_too_large",
                "prediction": {"debug_info": {}},
            }
        ),
        encoding="utf-8",
    )

    df = _load_records([f"bridge={root}"])
    grounding_dino_iou_analysis(df, base / "out", base / "fig")

    assert (base / "out" / "grounding_dino_iou_sweep.csv").exists()
