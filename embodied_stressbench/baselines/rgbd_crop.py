from __future__ import annotations

import os
import time
from typing import Any, Dict, Tuple

import numpy as np

from embodied_stressbench.baselines.base import TargetSourceBaseline
from embodied_stressbench.perception.depth_lifting import backproject_pixel, transform_camera_to_world
from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.detectors.clip_rerank import ClipRerankProvider
from embodied_stressbench.detectors.grounding_dino import GroundingDinoProvider
from embodied_stressbench.perception.detection_selection import select_detection, select_first_detection
from embodied_stressbench.types import Observation, TargetPrediction

_CLIP_PROVIDER: ClipRerankProvider | None = None
_CLIP_PROVIDER_ERROR: str | None = None
_GROUNDING_DINO_PROVIDER: GroundingDinoProvider | None = None
_GROUNDING_DINO_PROVIDER_ERROR: str | None = None


def _get_clip_provider() -> ClipRerankProvider | None:
    """Lazily construct CLIP once per worker process.

    The open-vocabulary baseline is optional. If the dependency stack or model
    cache is unavailable, experiments should record an explicit selection
    failure instead of silently pretending that CLIP was evaluated.
    """
    global _CLIP_PROVIDER, _CLIP_PROVIDER_ERROR
    if _CLIP_PROVIDER is not None:
        return _CLIP_PROVIDER
    if _CLIP_PROVIDER_ERROR is not None:
        return None
    try:
        _CLIP_PROVIDER = ClipRerankProvider()
    except Exception as exc:  # pragma: no cover - exercised on dependency-missing hosts
        _CLIP_PROVIDER_ERROR = f"{type(exc).__name__}: {exc}"
        return None
    return _CLIP_PROVIDER


def _select_clip_rerank_detection(
    observation: Observation,
    query: str,
) -> tuple[Dict[str, Any] | None, Dict[str, Any]]:
    provider = _get_clip_provider()
    if provider is None:
        return None, {
            "selection_strategy": "clip_rerank",
            "selection_failure_reason": "clip_rerank_unavailable",
            "clip_rerank_error": _CLIP_PROVIDER_ERROR,
            "num_candidate_detections": len(observation.detections),
        }

    result: DetectionProviderResult = provider.detect(observation, query)
    debug = {
        "selection_strategy": "clip_rerank",
        "selection_failure_reason": None,
        "num_candidate_detections": len(observation.detections),
        **result.debug_info,
    }
    if not result.detections:
        debug["selection_failure_reason"] = result.debug_info.get("reason", "clip_rerank_no_detection")
        return None, debug
    detection = result.detections[0]
    try:
        index = observation.detections.index(detection)
    except ValueError:
        index = next(
            (
                i
                for i, candidate in enumerate(observation.detections)
                if candidate.get("bbox_xyxy") == detection.get("bbox_xyxy")
                and candidate.get("label") == detection.get("label")
            ),
            None,
        )
    debug.update(
        {
            "selected_detection_index": index,
            "selected_detection_label": detection.get("label"),
            "selected_detection_is_target": bool(detection.get("is_target", False)),
            "selected_detection_distractor_type": detection.get("distractor_type"),
            "clip_score": detection.get("clip_score"),
        }
    )
    return detection, debug


def _get_grounding_dino_provider() -> GroundingDinoProvider | None:
    global _GROUNDING_DINO_PROVIDER, _GROUNDING_DINO_PROVIDER_ERROR
    if _GROUNDING_DINO_PROVIDER is not None:
        return _GROUNDING_DINO_PROVIDER
    retries = int(os.environ.get("EMBODIED_STRESSBENCH_GDINO_INIT_RETRIES", "3"))
    for attempt in range(max(1, retries)):
        try:
            _GROUNDING_DINO_PROVIDER = GroundingDinoProvider()
            _GROUNDING_DINO_PROVIDER_ERROR = None
            return _GROUNDING_DINO_PROVIDER
        except Exception as exc:  # pragma: no cover - exercised on dependency-missing hosts
            _GROUNDING_DINO_PROVIDER_ERROR = f"{type(exc).__name__}: {exc}"
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    return None


def _select_grounding_dino_detection(
    observation: Observation,
    query: str,
) -> tuple[Dict[str, Any] | None, Dict[str, Any]]:
    provider = _get_grounding_dino_provider()
    if provider is None:
        return None, {
            "selection_strategy": "grounding_dino",
            "selection_failure_reason": "grounding_dino_unavailable",
            "grounding_dino_error": _GROUNDING_DINO_PROVIDER_ERROR,
            "num_candidate_detections": len(observation.detections),
        }
    result: DetectionProviderResult = provider.detect(observation, query)
    debug = {
        "selection_strategy": "grounding_dino",
        "selection_failure_reason": None,
        "num_candidate_detections": len(observation.detections),
        **result.debug_info,
    }
    if not result.detections:
        debug["selection_failure_reason"] = result.debug_info.get("reason", "grounding_dino_no_detection")
        return None, debug
    detection = result.detections[0]
    debug.update(
        {
            "selected_detection_index": 0,
            "selected_detection_label": detection.get("label"),
            "selected_detection_is_target": bool(detection.get("is_target", False)),
            "selected_detection_distractor_type": detection.get("distractor_type"),
            "grounding_dino_score": detection.get("score"),
            "grounding_dino_target_iou": detection.get("target_iou"),
        }
    )
    return detection, debug


def _selected_detection_bbox(
    observation: Observation,
    query: str,
    strategy: str = "query_aware",
) -> tuple[Tuple[int, int, int, int] | None, Dict[str, Any]]:
    if strategy == "first_detection":
        detection, selection_debug = select_first_detection(observation, query)
    elif strategy == "query_aware":
        detection, selection_debug = select_detection(observation, query)
        selection_debug["selection_strategy"] = "query_aware"
    elif strategy == "clip_rerank":
        detection, selection_debug = _select_clip_rerank_detection(observation, query)
    elif strategy == "grounding_dino":
        detection, selection_debug = _select_grounding_dino_detection(observation, query)
    elif strategy == "oracle_2d_box":
        detection = next((det for det in observation.detections if det.get("is_target")), None)
        if detection is None and observation.object_metadata.get("target_bbox_xyxy") is not None:
            detection = {
                "label": observation.object_metadata.get("target_label", "oracle_target"),
                "bbox_xyxy": observation.object_metadata.get("target_bbox_xyxy"),
                "score": 1.0,
                "source": "oracle_2d_box",
                "is_target": True,
                "distractor_type": None,
            }
        if detection is None:
            selection_debug = {
                "selection_strategy": "oracle_2d_box",
                "selection_failure_reason": "oracle_2d_box_unavailable",
                "num_candidate_detections": len(observation.detections),
            }
        else:
            try:
                index = observation.detections.index(detection)
            except ValueError:
                index = None
            selection_debug = {
                "selection_strategy": "oracle_2d_box",
                "selected_detection_index": index,
                "selected_detection_label": detection.get("label"),
                "selected_detection_is_target": bool(detection.get("is_target", False)),
                "selected_detection_distractor_type": detection.get("distractor_type"),
                "selection_failure_reason": None,
                "num_candidate_detections": len(observation.detections),
            }
    else:
        raise ValueError(f"Unknown detection selection strategy: {strategy}")
    if detection is None:
        return None, selection_debug
    bbox = detection.get("bbox_xyxy")
    if bbox is None:
        selection_debug["selection_failure_reason"] = "selected_detection_missing_bbox"
        return None, selection_debug
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    return (x1, y1, x2, y2), selection_debug


def _valid_crop_depths(observation: Observation, bbox: Tuple[int, int, int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if observation.depth is None:
        return np.array([]), np.array([]), np.array([])
    x1, y1, x2, y2 = bbox
    depth = observation.depth[y1:y2, x1:x2]
    yy, xx = np.mgrid[y1:y2, x1:x2]
    mask = np.isfinite(depth) & (depth > 0)
    return depth[mask], xx[mask], yy[mask]


class BoxCenterDepthBaseline(TargetSourceBaseline):
    name = "box_center_depth"
    selection_strategy = "query_aware"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox, selection_debug = _selected_detection_bbox(observation, query, self.selection_strategy)
        if bbox is None:
            return TargetPrediction(None, 0.0, selection_debug, "no_detection")
        if observation.depth is None or observation.intrinsics is None:
            return TargetPrediction(None, 0.0, selection_debug, "missing_depth_or_intrinsics")
        x1, y1, x2, y2 = bbox
        u = int(round((x1 + x2) / 2))
        v = int(round((y1 + y2) / 2))
        d = float(observation.depth[v, u])
        try:
            pc = backproject_pixel(u, v, d, observation.intrinsics)
        except ValueError as e:
            return TargetPrediction(None, 0.0, {"bbox": bbox, "u": u, "v": v, **selection_debug}, str(e))
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(pw, 0.6, {"bbox": bbox, "pixel": [u, v], "depth": d, **selection_debug})


class CropMedianDepthBaseline(TargetSourceBaseline):
    name = "crop_median_depth"
    selection_strategy = "query_aware"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox, selection_debug = _selected_detection_bbox(observation, query, self.selection_strategy)
        if bbox is None:
            return TargetPrediction(None, 0.0, selection_debug, "no_detection")
        if observation.intrinsics is None:
            return TargetPrediction(None, 0.0, selection_debug, "missing_intrinsics")
        depths, xs, ys = _valid_crop_depths(observation, bbox)
        if len(depths) == 0:
            return TargetPrediction(None, 0.0, {"bbox": bbox, **selection_debug}, "no_valid_depth_in_crop")
        idx = int(np.argsort(depths)[len(depths) // 2])
        d = float(depths[idx])
        u = float(xs[idx])
        v = float(ys[idx])
        pc = backproject_pixel(u, v, d, observation.intrinsics)
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(
            pw,
            0.7,
            {"bbox": bbox, "pixel": [u, v], "depth": d, "num_valid": int(len(depths)), **selection_debug},
        )


class CropTrimmedMedianDepthBaseline(TargetSourceBaseline):
    name = "crop_trimmed_median_depth"
    selection_strategy = "query_aware"
    trim_fraction = 0.10

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox, selection_debug = _selected_detection_bbox(observation, query, self.selection_strategy)
        if bbox is None:
            return TargetPrediction(None, 0.0, selection_debug, "no_detection")
        if observation.intrinsics is None:
            return TargetPrediction(None, 0.0, selection_debug, "missing_intrinsics")
        depths, xs, ys = _valid_crop_depths(observation, bbox)
        n = len(depths)
        if n == 0:
            return TargetPrediction(None, 0.0, {"bbox": bbox, **selection_debug}, "no_valid_depth_in_crop")
        order = np.argsort(depths)
        trim = int(np.floor(n * self.trim_fraction))
        if n - 2 * trim <= 0:
            trim = 0
        kept = order[trim : n - trim]
        idx = int(kept[len(kept) // 2])
        d = float(depths[idx])
        u = float(xs[idx])
        v = float(ys[idx])
        pc = backproject_pixel(u, v, d, observation.intrinsics)
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(
            pw,
            0.72,
            {
                "bbox": bbox,
                "pixel": [u, v],
                "depth": d,
                "num_valid": int(n),
                "trim_fraction": float(self.trim_fraction),
                "num_trimmed_each_side": int(trim),
                **selection_debug,
            },
        )


class CropTopSurfaceBaseline(TargetSourceBaseline):
    name = "crop_top_surface"
    selection_strategy = "query_aware"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox, selection_debug = _selected_detection_bbox(observation, query, self.selection_strategy)
        if bbox is None:
            return TargetPrediction(None, 0.0, selection_debug, "no_detection")
        if observation.intrinsics is None:
            return TargetPrediction(None, 0.0, selection_debug, "missing_intrinsics")
        depths, xs, ys = _valid_crop_depths(observation, bbox)
        if len(depths) == 0:
            return TargetPrediction(None, 0.0, {"bbox": bbox, **selection_debug}, "no_valid_depth_in_crop")
        # For a front-facing depth camera, smaller depth is closer/top-surface-like in this mock setup.
        idx = int(np.argmin(depths))
        d = float(depths[idx])
        u = float(xs[idx])
        v = float(ys[idx])
        pc = backproject_pixel(u, v, d, observation.intrinsics)
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(
            pw,
            0.65,
            {"bbox": bbox, "pixel": [u, v], "depth": d, "num_valid": int(len(depths)), **selection_debug},
        )


class BoxCenterDepthQueryAwareBaseline(BoxCenterDepthBaseline):
    name = "box_center_depth_query_aware"


class CropMedianDepthQueryAwareBaseline(CropMedianDepthBaseline):
    name = "crop_median_depth_query_aware"


class CropTrimmedMedianDepthQueryAwareBaseline(CropTrimmedMedianDepthBaseline):
    name = "crop_trimmed_median_depth_query_aware"


class CropTopSurfaceQueryAwareBaseline(CropTopSurfaceBaseline):
    name = "crop_top_surface_query_aware"


class BoxCenterDepthFirstDetectionBaseline(BoxCenterDepthBaseline):
    name = "box_center_depth_first_detection"
    selection_strategy = "first_detection"


class CropMedianDepthFirstDetectionBaseline(CropMedianDepthBaseline):
    name = "crop_median_depth_first_detection"
    selection_strategy = "first_detection"


class CropTrimmedMedianDepthFirstDetectionBaseline(CropTrimmedMedianDepthBaseline):
    name = "crop_trimmed_median_depth_first_detection"
    selection_strategy = "first_detection"


class CropTopSurfaceFirstDetectionBaseline(CropTopSurfaceBaseline):
    name = "crop_top_surface_first_detection"
    selection_strategy = "first_detection"


class BoxCenterDepthOracle2DBoxBaseline(BoxCenterDepthBaseline):
    name = "box_center_depth_oracle_2d_box"
    selection_strategy = "oracle_2d_box"


class CropMedianDepthOracle2DBoxBaseline(CropMedianDepthBaseline):
    name = "crop_median_depth_oracle_2d_box"
    selection_strategy = "oracle_2d_box"


class CropTrimmedMedianDepthOracle2DBoxBaseline(CropTrimmedMedianDepthBaseline):
    name = "crop_trimmed_median_depth_oracle_2d_box"
    selection_strategy = "oracle_2d_box"


class BoxCenterDepthClipRerankBaseline(BoxCenterDepthBaseline):
    name = "box_center_depth_clip_rerank"
    selection_strategy = "clip_rerank"


class CropMedianDepthClipRerankBaseline(CropMedianDepthBaseline):
    name = "crop_median_depth_clip_rerank"
    selection_strategy = "clip_rerank"


class BoxCenterDepthGroundingDinoBaseline(BoxCenterDepthBaseline):
    name = "box_center_depth_grounding_dino"
    selection_strategy = "grounding_dino"


class CropMedianDepthGroundingDinoBaseline(CropMedianDepthBaseline):
    name = "crop_median_depth_grounding_dino"
    selection_strategy = "grounding_dino"


class CropTrimmedMedianDepthGroundingDinoBaseline(CropTrimmedMedianDepthBaseline):
    name = "crop_trimmed_median_depth_grounding_dino"
    selection_strategy = "grounding_dino"
