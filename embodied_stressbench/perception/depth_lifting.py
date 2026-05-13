from __future__ import annotations

import numpy as np


def backproject_pixel(u: float, v: float, depth: float, intrinsics: np.ndarray) -> np.ndarray:
    """Back-project one pixel to camera-frame 3D coordinates."""
    if depth is None or not np.isfinite(depth) or depth <= 0:
        raise ValueError(f"Invalid depth: {depth}")
    fx = intrinsics[0, 0]
    fy = intrinsics[1, 1]
    cx = intrinsics[0, 2]
    cy = intrinsics[1, 2]
    x = (u - cx) * depth / fx
    y = (v - cy) * depth / fy
    z = depth
    return np.array([x, y, z], dtype=float)


def transform_camera_to_world(point_camera: np.ndarray, extrinsics: np.ndarray | None) -> np.ndarray:
    if extrinsics is None:
        return point_camera
    p = np.ones(4, dtype=float)
    p[:3] = point_camera
    return (extrinsics @ p)[:3]
