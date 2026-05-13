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

    raise ValueError(f"Unknown stressor: {stressor_name}")
