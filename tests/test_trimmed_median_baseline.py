from __future__ import annotations

import numpy as np

from embodied_stressbench.baselines import get_baseline
from embodied_stressbench.types import Observation


def _obs(depth_crop: np.ndarray) -> Observation:
    depth = np.ones((8, 8), dtype=np.float32)
    depth[2:6, 2:6] = depth_crop.astype(np.float32)
    return Observation(
        rgb=np.zeros((8, 8, 3), dtype=np.uint8),
        depth=depth,
        intrinsics=np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 1.0]]),
        extrinsics=np.eye(4),
        detections=[
            {
                "label": "target object",
                "bbox_xyxy": [2, 2, 6, 6],
                "score": 1.0,
                "is_target": True,
                "query_aliases": ["target object"],
            }
        ],
    )


def test_trimmed_median_baselines_are_registered():
    assert get_baseline("crop_trimmed_median_depth").name == "crop_trimmed_median_depth"
    assert get_baseline("crop_trimmed_median_depth_query_aware").name == "crop_trimmed_median_depth_query_aware"
    assert get_baseline("crop_trimmed_median_depth_first_detection").name == "crop_trimmed_median_depth_first_detection"
    assert get_baseline("crop_trimmed_median_depth_grounding_dino").name == "crop_trimmed_median_depth_grounding_dino"


def test_trimmed_median_ignores_depth_outliers():
    crop = np.array(
        [
            [0.10, 0.48, 0.49, 0.50],
            [0.50, 0.51, 0.52, 0.53],
            [0.54, 0.55, 0.56, 0.57],
            [0.58, 0.59, 0.60, 5.00],
        ],
        dtype=np.float32,
    )
    pred = get_baseline("crop_trimmed_median_depth").predict_target(_obs(crop), "target object", {})
    assert pred.failure_reason is None
    assert 0.50 <= pred.debug_info["depth"] <= 0.58
    assert pred.debug_info["num_trimmed_each_side"] == 1


def test_trimmed_median_handles_sparse_depth():
    crop = np.zeros((4, 4), dtype=np.float32)
    crop[0, 0] = 0.4
    crop[1, 1] = 0.5
    crop[2, 2] = 0.6
    pred = get_baseline("crop_trimmed_median_depth").predict_target(_obs(crop), "target object", {})
    assert pred.failure_reason is None
    assert pred.debug_info["num_valid"] == 3


def test_trimmed_median_reports_no_valid_depth():
    crop = np.zeros((4, 4), dtype=np.float32)
    pred = get_baseline("crop_trimmed_median_depth").predict_target(_obs(crop), "target object", {})
    assert pred.target_3d is None
    assert pred.failure_reason == "no_valid_depth_in_crop"
