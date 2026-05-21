from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from embodied_stressbench.types import Observation
from embodied_stressbench.utils.seeds import make_rng


def _copy_observation(obs: Observation) -> Observation:
    return Observation(
        rgb=None if obs.rgb is None else obs.rgb.copy(),
        depth=None if obs.depth is None else obs.depth.copy(),
        intrinsics=None if obs.intrinsics is None else obs.intrinsics.copy(),
        extrinsics=None if obs.extrinsics is None else obs.extrinsics.copy(),
        detections=[dict(d) for d in obs.detections],
        object_metadata=dict(obs.object_metadata),
        debug_info=dict(obs.debug_info),
    )


def _target_detection_index(obs: Observation) -> int:
    for idx, detection in enumerate(obs.detections):
        if detection.get("is_target"):
            return idx
    return 0


def _bbox_clip(bbox: list[int], shape: tuple[int, int]) -> list[int]:
    h, w = shape
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1 = int(np.clip(x1, 0, max(0, w - 1)))
    y1 = int(np.clip(y1, 0, max(0, h - 1)))
    x2 = int(np.clip(x2, x1 + 1, w))
    y2 = int(np.clip(y2, y1 + 1, h))
    return [x1, y1, x2, y2]


def _shift_bbox(bbox: list[int], shape: tuple[int, int], level: int) -> list[int]:
    x1, y1, x2, y2 = [int(v) for v in bbox]
    width = max(1, x2 - x1)
    height = max(1, y2 - y1)
    frac_by_level = {0: 0.0, 1: 0.45, 2: 0.80, 3: 1.20}
    shift = frac_by_level.get(level, 1.20)
    return _bbox_clip([x1 + int(width * shift), y1, x2 + int(width * shift), y2], shape)


def _insert_distractor(obs: Observation, level: int, distractor_type: str, label: str) -> Dict[str, Any]:
    if not obs.detections:
        return {"inserted": False, "reason": "no_detection"}
    target_idx = _target_detection_index(obs)
    target = dict(obs.detections[target_idx])
    if obs.depth is not None:
        image_shape = obs.depth.shape[:2]
    elif obs.rgb is not None:
        image_shape = obs.rgb.shape[:2]
    else:
        image_shape = (128, 128)
    target_bbox = target.get("bbox_xyxy", [0, 0, image_shape[1], image_shape[0]])
    distractor_bbox = _shift_bbox(target_bbox, image_shape, level)
    distractor = {
        **target,
        "label": label,
        "bbox_xyxy": distractor_bbox,
        "score": float(target.get("score", 1.0)) + 0.05,
        "is_target": False,
        "distractor_type": distractor_type,
        "query_aliases": target.get("query_aliases", []),
    }
    obs.detections = [distractor] + [dict(d) for d in obs.detections]
    return {
        "inserted": True,
        "target_bbox_xyxy": target_bbox,
        "distractor_bbox_xyxy": distractor_bbox,
        "distractor_type": distractor_type,
        "distractor_label": label,
    }


def _target_bbox(obs: Observation) -> list[int] | None:
    if not obs.detections:
        return None
    bbox = obs.detections[_target_detection_index(obs)].get("bbox_xyxy")
    if bbox is None:
        return None
    return [int(round(v)) for v in bbox]


def _occlude_target_crop(obs: Observation, level: int) -> Dict[str, Any]:
    frac_by_level = {0: 0.0, 1: 0.25, 2: 0.50, 3: 0.75}
    frac = frac_by_level.get(level, 0.75)
    bbox = _target_bbox(obs)
    params: Dict[str, Any] = {"occlusion_fraction": frac, "target_bbox_xyxy": bbox}
    if bbox is not None and frac > 0 and (obs.rgb is not None or obs.depth is not None):
        shape = obs.depth.shape[:2] if obs.depth is not None else obs.rgb.shape[:2]
        x1, y1, x2, y2 = _bbox_clip(bbox, shape)
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        occ_w = max(1, int(w * frac))
        occ_h = max(1, int(h * frac))
        ox1 = x1 + (w - occ_w) // 2
        oy1 = y1 + (h - occ_h) // 2
        ox2 = ox1 + occ_w
        oy2 = oy1 + occ_h
        if obs.rgb is not None:
            obs.rgb[oy1:oy2, ox1:ox2] = 0
        if obs.depth is not None:
            obs.depth[oy1:oy2, ox1:ox2] = 0.0
        params["occlusion_xyxy"] = [ox1, oy1, ox2, oy2]
    return params


def apply_stressor(
    observation: Observation,
    query: str,
    stressor_name: str,
    level: int,
    seed: int,
) -> Tuple[Observation, str, Dict[str, Any]]:
    """Apply one deterministic stressor and return obs, query, stress_info."""
    rng = make_rng(seed + 1009 * level)
    obs = _copy_observation(observation)
    info: Dict[str, Any] = {"name": stressor_name, "level": int(level)}

    if stressor_name in ("none", None):
        info["params"] = {}
        return obs, query, info

    if stressor_name == "depth_noise":
        sigma_by_level = {0: 0.0, 1: 0.003, 2: 0.008, 3: 0.015}
        missing_by_level = {0: 0.0, 1: 0.02, 2: 0.08, 3: 0.15}
        sigma = sigma_by_level.get(level, 0.015)
        missing_prob = missing_by_level.get(level, 0.15)
        if obs.depth is not None:
            noise = rng.normal(0.0, sigma, size=obs.depth.shape)
            missing = rng.random(obs.depth.shape) < missing_prob
            obs.depth = obs.depth + noise
            obs.depth[missing] = 0.0
        info["params"] = {"sigma": sigma, "missing_prob": missing_prob}
        return obs, query, info

    if stressor_name == "visual_occlusion":
        frac_by_level = {0: 0.0, 1: 0.05, 2: 0.15, 3: 0.30}
        frac = frac_by_level.get(level, 0.30)
        if obs.rgb is not None and frac > 0:
            h, w = obs.rgb.shape[:2]
            occ_h = max(1, int(h * frac))
            occ_w = max(1, int(w * frac))
            y = int(rng.integers(0, max(1, h - occ_h)))
            x = int(rng.integers(0, max(1, w - occ_w)))
            obs.rgb[y : y + occ_h, x : x + occ_w] = 0
            if obs.depth is not None:
                obs.depth[y : y + occ_h, x : x + occ_w] = 0.0
            info["params"] = {"occlusion_fraction": frac, "xywh": [x, y, occ_w, occ_h]}
        else:
            info["params"] = {"occlusion_fraction": frac}
        return obs, query, info

    if stressor_name == "partial_target_occlusion":
        info["params"] = _occlude_target_crop(obs, level)
        return obs, query, info

    if stressor_name == "depth_sparsity":
        missing_by_level = {0: 0.0, 1: 0.25, 2: 0.50, 3: 0.75}
        missing_prob = missing_by_level.get(level, 0.75)
        bbox = _target_bbox(obs)
        removed = 0
        total = 0
        if obs.depth is not None and bbox is not None and missing_prob > 0:
            x1, y1, x2, y2 = _bbox_clip(bbox, obs.depth.shape[:2])
            crop = obs.depth[y1:y2, x1:x2]
            valid = np.isfinite(crop) & (crop > 0)
            missing = (rng.random(crop.shape) < missing_prob) & valid
            removed = int(np.count_nonzero(missing))
            total = int(np.count_nonzero(valid))
            crop[missing] = 0.0
        info["params"] = {"missing_prob": missing_prob, "target_bbox_xyxy": bbox, "removed_valid_depth": removed, "total_valid_depth": total}
        return obs, query, info

    if stressor_name == "semantic_variants":
        variants = {
            0: query,
            1: query.replace("pick", "grasp").replace("red", "crimson"),
            2: "pick the object",
            3: "pick the cube near the distractor",
        }
        new_query = variants.get(level, query)
        info["params"] = {"original_query": query, "new_query": new_query}
        return obs, new_query, info

    if stressor_name == "same_shape_distractor":
        params = _insert_distractor(obs, level, "same_shape", "target-shaped distractor")
        info["params"] = params
        return obs, query, info

    if stressor_name == "same_color_distractor":
        params = _insert_distractor(obs, level, "same_color", "red target distractor")
        info["params"] = params
        return obs, query, info

    if stressor_name == "nearby_distractor":
        params = _insert_distractor(obs, level, "nearby_object", "nearby target object")
        info["params"] = params
        return obs, query, info

    if stressor_name == "same_color_partial_occlusion":
        distractor_params = _insert_distractor(obs, level, "same_color_partial_occlusion", "red target distractor")
        occlusion_params = _occlude_target_crop(obs, level)
        info["params"] = {"distractor": distractor_params, "occlusion": occlusion_params}
        return obs, query, info

    if stressor_name == "same_shape_nearby_occlusion":
        distractor_params = _insert_distractor(obs, level, "same_shape_nearby_occlusion", "target-shaped nearby object")
        occlusion_params = _occlude_target_crop(obs, level)
        info["params"] = {"distractor": distractor_params, "occlusion": occlusion_params}
        return obs, query, info

    if stressor_name == "camera_pose_noise":
        translation_by_level = {0: 0.0, 1: 0.002, 2: 0.005, 3: 0.01}
        std = translation_by_level.get(level, 0.01)
        if obs.extrinsics is not None:
            obs.extrinsics[:3, 3] += rng.normal(0.0, std, size=3)
        info["params"] = {"translation_std": std, "rotation_noise_not_implemented": True}
        return obs, query, info

    if stressor_name == "execution_offset":
        # This stressor is consumed by the runner after target prediction.
        offset_std_by_level = {0: 0.0, 1: 0.005, 2: 0.015, 3: 0.03}
        offset_std = offset_std_by_level.get(level, 0.03)
        offset = rng.normal(0.0, offset_std, size=3).tolist()
        info["params"] = {"offset_std": offset_std, "execution_offset": offset}
        return obs, query, info

    if stressor_name == "execution_offset_strong":
        offset_std_by_level = {0: 0.0, 1: 0.015, 2: 0.035, 3: 0.06}
        offset_std = offset_std_by_level.get(level, 0.06)
        offset = rng.normal(0.0, offset_std, size=3).tolist()
        info["params"] = {"offset_std": offset_std, "execution_offset": offset}
        return obs, query, info

    raise ValueError(f"Unknown stressor: {stressor_name}")
