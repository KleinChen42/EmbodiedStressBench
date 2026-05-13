from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from embodied_stressbench.baselines.base import TargetSourceBaseline
from embodied_stressbench.perception.depth_lifting import backproject_pixel, transform_camera_to_world
from embodied_stressbench.types import Observation, TargetPrediction


def _first_detection_bbox(observation: Observation) -> Tuple[int, int, int, int] | None:
    if not observation.detections:
        return None
    bbox = observation.detections[0].get("bbox_xyxy")
    if bbox is None:
        return None
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    return x1, y1, x2, y2


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

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox = _first_detection_bbox(observation)
        if bbox is None:
            return TargetPrediction(None, 0.0, {}, "no_detection")
        if observation.depth is None or observation.intrinsics is None:
            return TargetPrediction(None, 0.0, {}, "missing_depth_or_intrinsics")
        x1, y1, x2, y2 = bbox
        u = int(round((x1 + x2) / 2))
        v = int(round((y1 + y2) / 2))
        d = float(observation.depth[v, u])
        try:
            pc = backproject_pixel(u, v, d, observation.intrinsics)
        except ValueError as e:
            return TargetPrediction(None, 0.0, {"bbox": bbox, "u": u, "v": v}, str(e))
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(pw, 0.6, {"bbox": bbox, "pixel": [u, v], "depth": d})


class CropMedianDepthBaseline(TargetSourceBaseline):
    name = "crop_median_depth"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox = _first_detection_bbox(observation)
        if bbox is None:
            return TargetPrediction(None, 0.0, {}, "no_detection")
        if observation.intrinsics is None:
            return TargetPrediction(None, 0.0, {}, "missing_intrinsics")
        depths, xs, ys = _valid_crop_depths(observation, bbox)
        if len(depths) == 0:
            return TargetPrediction(None, 0.0, {"bbox": bbox}, "no_valid_depth_in_crop")
        idx = int(np.argsort(depths)[len(depths) // 2])
        d = float(depths[idx])
        u = float(xs[idx])
        v = float(ys[idx])
        pc = backproject_pixel(u, v, d, observation.intrinsics)
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(pw, 0.7, {"bbox": bbox, "pixel": [u, v], "depth": d, "num_valid": int(len(depths))})


class CropTopSurfaceBaseline(TargetSourceBaseline):
    name = "crop_top_surface"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        bbox = _first_detection_bbox(observation)
        if bbox is None:
            return TargetPrediction(None, 0.0, {}, "no_detection")
        if observation.intrinsics is None:
            return TargetPrediction(None, 0.0, {}, "missing_intrinsics")
        depths, xs, ys = _valid_crop_depths(observation, bbox)
        if len(depths) == 0:
            return TargetPrediction(None, 0.0, {"bbox": bbox}, "no_valid_depth_in_crop")
        # For a front-facing depth camera, smaller depth is closer/top-surface-like in this mock setup.
        idx = int(np.argmin(depths))
        d = float(depths[idx])
        u = float(xs[idx])
        v = float(ys[idx])
        pc = backproject_pixel(u, v, d, observation.intrinsics)
        pw = transform_camera_to_world(pc, observation.extrinsics)
        return TargetPrediction(pw, 0.65, {"bbox": bbox, "pixel": [u, v], "depth": d, "num_valid": int(len(depths))})
