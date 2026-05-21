import numpy as np

from embodied_stressbench.stressors import apply_stressor
from embodied_stressbench.types import Observation


def _obs():
    return Observation(
        rgb=np.ones((20, 20, 3), dtype=np.uint8) * 255,
        depth=np.ones((20, 20), dtype=np.float32),
        intrinsics=np.eye(3),
        extrinsics=np.eye(4),
        detections=[
            {
                "label": "target object",
                "bbox_xyxy": [5, 5, 15, 15],
                "score": 1.0,
                "is_target": True,
                "query_aliases": ["target object"],
            }
        ],
        object_metadata={"oracle_target_3d": [0, 0, 0]},
    )


def test_nearby_distractor_inserts_non_target_first():
    obs, _, info = apply_stressor(_obs(), "pick the target object", "nearby_distractor", 2, 0)
    assert info["params"]["inserted"]
    assert len(obs.detections) == 2
    assert obs.detections[0]["is_target"] is False
    assert obs.detections[0]["distractor_type"] == "nearby_object"


def test_partial_target_occlusion_zeroes_target_crop_depth():
    obs, _, info = apply_stressor(_obs(), "pick the target object", "partial_target_occlusion", 2, 0)
    x1, y1, x2, y2 = info["params"]["occlusion_xyxy"]
    assert np.all(obs.depth[y1:y2, x1:x2] == 0.0)


def test_depth_sparsity_removes_some_target_depth():
    obs, _, info = apply_stressor(_obs(), "pick the target object", "depth_sparsity", 3, 0)
    assert info["params"]["removed_valid_depth"] > 0
    assert np.count_nonzero(obs.depth[5:15, 5:15] == 0.0) > 0


def test_same_color_partial_occlusion_inserts_distractor_and_occludes_target():
    obs, _, info = apply_stressor(_obs(), "pick the target object", "same_color_partial_occlusion", 3, 0)
    assert info["params"]["distractor"]["inserted"]
    assert obs.detections[0]["is_target"] is False
    assert obs.detections[0]["distractor_type"] == "same_color_partial_occlusion"
    x1, y1, x2, y2 = info["params"]["occlusion"]["occlusion_xyxy"]
    assert np.all(obs.depth[y1:y2, x1:x2] == 0.0)


def test_same_shape_nearby_occlusion_inserts_distractor_and_occludes_target():
    obs, _, info = apply_stressor(_obs(), "pick the target object", "same_shape_nearby_occlusion", 3, 0)
    assert info["params"]["distractor"]["inserted"]
    assert obs.detections[0]["is_target"] is False
    assert obs.detections[0]["distractor_type"] == "same_shape_nearby_occlusion"
    x1, y1, x2, y2 = info["params"]["occlusion"]["occlusion_xyxy"]
    assert np.all(obs.depth[y1:y2, x1:x2] == 0.0)


def test_semantic_distractor_shift_is_bbox_width_fraction():
    obs, _, info = apply_stressor(_obs(), "pick the target object", "same_shape_distractor", 2, 0)
    target = info["params"]["target_bbox_xyxy"]
    distractor = info["params"]["distractor_bbox_xyxy"]
    width = target[2] - target[0]
    assert distractor[0] - target[0] == int(width * 0.80)
    assert obs.detections[0]["is_target"] is False
    assert obs.detections[1]["is_target"] is True
