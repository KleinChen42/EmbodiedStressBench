from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_benchmark_comparison_table import ROWS, _write_tex
from scripts.generate_ieee_access_qualitative_figures import _read_records, _save_figure, _select_cases


def _write_case(path: Path, **overrides):
    item = {
        "task": "PickCube",
        "baseline": "crop_median_depth_grounding_dino",
        "stressor": "partial_target_occlusion",
        "level": 2,
        "seed": 0,
        "success": True,
        "failure_type": None,
        "target_error_l2": 0.04,
        "prediction": {
            "debug_info": {
                "bbox": [20, 30, 90, 110],
                "pixel": [55, 70],
                "grounding_dino_target_iou": 0.12,
                "selected_detection_is_target": True,
            }
        },
    }
    item.update(overrides)
    path.write_text(json.dumps(item), encoding="utf-8")


def test_qualitative_case_selection_and_figure():
    base = Path("ieee_access_revision_20260520/test_tmp_qualitative")
    root = base / "run"
    root.mkdir(parents=True, exist_ok=True)
    _write_case(root / "success.json")
    _write_case(
        root / "wrong_detection.json",
        baseline="crop_median_depth_first_detection",
        success=False,
        failure_type="wrong_detection_selected",
        target_error_l2=0.24,
        prediction={"debug_info": {"bbox": [10, 10, 50, 60], "selected_detection_is_target": False}},
    )
    _write_case(
        root / "depth.json",
        success=False,
        failure_type="depth_invalid",
        target_error_l2=None,
        prediction={"debug_info": {"bbox": [15, 20, 75, 95]}},
    )

    df = _read_records([f"bridge={root}"])
    cases = _select_cases(df)
    assert not cases.empty
    assert "Low 2D IoU, valid 3D target" in set(cases["case_label"])

    fig_dir = base / "figures"
    _save_figure(cases, fig_dir)
    assert (fig_dir / "qualitative_failure_teaser.pdf").exists()
    assert (fig_dir / "qualitative_failure_teaser.png").exists()


def test_benchmark_comparison_table_contains_core_rows():
    import pandas as pd

    base = Path("ieee_access_revision_20260520/test_tmp_qualitative")
    base.mkdir(parents=True, exist_ok=True)
    out = base / "comparison.tex"
    _write_tex(pd.DataFrame(ROWS), out)
    text = out.read_text(encoding="utf-8")
    assert "EmbodiedStressBench" in text
    assert "ManiSkill" in text
    assert "VLABench" in text
    assert r"\cite{gu2021maniskill,gu2023maniskill2}" in text
