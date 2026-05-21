import numpy as np

from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.baselines import get_baseline
from embodied_stressbench.baselines import rgbd_crop
from embodied_stressbench.perception.detection_selection import select_detection, select_first_detection
from embodied_stressbench.types import Observation


def _obs(detections):
    return Observation(
        rgb=np.zeros((16, 16, 3), dtype=np.uint8),
        depth=np.ones((16, 16), dtype=np.float32),
        intrinsics=np.eye(3),
        extrinsics=np.eye(4),
        detections=detections,
    )


def test_select_detection_prefers_query_match():
    obs = _obs(
        [
            {"label": "blue distractor", "bbox_xyxy": [0, 0, 4, 4], "score": 1.0},
            {"label": "red cube", "bbox_xyxy": [4, 4, 8, 8], "score": 0.9, "is_target": True},
        ]
    )
    det, debug = select_detection(obs, "pick the red cube")
    assert det["label"] == "red cube"
    assert debug["selected_detection_index"] == 1


def test_select_detection_falls_back_to_first_without_match():
    obs = _obs(
        [
            {"label": "unknown one", "bbox_xyxy": [0, 0, 4, 4], "score": 1.0},
            {"label": "unknown two", "bbox_xyxy": [4, 4, 8, 8], "score": 0.9},
        ]
    )
    det, debug = select_detection(obs, "grasp banana")
    assert det["label"] == "unknown one"
    assert debug["selection_failure_reason"] == "no_query_match_fallback_first_detection"


def test_select_first_detection_ignores_query_match():
    obs = _obs(
        [
            {"label": "red distractor", "bbox_xyxy": [0, 0, 4, 4], "score": 1.0, "is_target": False},
            {"label": "target object", "bbox_xyxy": [4, 4, 8, 8], "score": 0.9, "is_target": True},
        ]
    )
    det, debug = select_first_detection(obs, "pick the target object")
    assert det["label"] == "red distractor"
    assert debug["selected_detection_index"] == 0
    assert debug["selected_detection_is_target"] is False
    assert debug["selection_strategy"] == "first_detection"


def test_clip_rerank_baseline_is_registered():
    assert get_baseline("box_center_depth_clip_rerank").name == "box_center_depth_clip_rerank"
    assert get_baseline("crop_median_depth_clip_rerank").name == "crop_median_depth_clip_rerank"
    assert get_baseline("box_center_depth_grounding_dino").name == "box_center_depth_grounding_dino"
    assert get_baseline("crop_median_depth_grounding_dino").name == "crop_median_depth_grounding_dino"


def test_clip_rerank_selection_uses_provider_order(monkeypatch):
    class FakeClipProvider:
        def detect(self, observation, query):
            return DetectionProviderResult(
                detections=[dict(observation.detections[1], clip_score=3.14)],
                debug_info={"provider": "fake_clip", "model_name": "fake"},
            )

    monkeypatch.setattr(rgbd_crop, "_CLIP_PROVIDER", FakeClipProvider())
    monkeypatch.setattr(rgbd_crop, "_CLIP_PROVIDER_ERROR", None)
    obs = _obs(
        [
            {"label": "distractor", "bbox_xyxy": [0, 0, 4, 4], "score": 1.0, "is_target": False},
            {"label": "target", "bbox_xyxy": [4, 4, 8, 8], "score": 0.9, "is_target": True},
        ]
    )

    bbox, debug = rgbd_crop._selected_detection_bbox(obs, "pick the target object", "clip_rerank")

    assert bbox == (4, 4, 8, 8)
    assert debug["selection_strategy"] == "clip_rerank"
    assert debug["provider"] == "fake_clip"
    assert debug["selected_detection_is_target"] is True


def test_grounding_dino_selection_uses_provider_box(monkeypatch):
    class FakeGroundingDinoProvider:
        def detect(self, observation, query):
            return DetectionProviderResult(
                detections=[
                    {
                        "label": "red cube",
                        "bbox_xyxy": [2, 3, 6, 7],
                        "score": 0.5,
                        "is_target": True,
                        "target_iou": 0.8,
                    }
                ],
                debug_info={"provider": "fake_grounding_dino", "model_name": "fake", "num_detections": 1},
            )

    monkeypatch.setattr(rgbd_crop, "_GROUNDING_DINO_PROVIDER", FakeGroundingDinoProvider())
    monkeypatch.setattr(rgbd_crop, "_GROUNDING_DINO_PROVIDER_ERROR", None)
    obs = _obs([{"label": "metadata box", "bbox_xyxy": [0, 0, 4, 4], "score": 1.0, "is_target": True}])

    bbox, debug = rgbd_crop._selected_detection_bbox(obs, "red cube", "grounding_dino")

    assert bbox == (2, 3, 6, 7)
    assert debug["selection_strategy"] == "grounding_dino"
    assert debug["provider"] == "fake_grounding_dino"
    assert debug["grounding_dino_target_iou"] == 0.8
