from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np

from embodied_stressbench.types import Observation
from embodied_stressbench.utils.seeds import make_rng


@dataclass
class ExecutionResult:
    success: bool
    failure_type: str | None
    debug_info: Dict[str, Any]


class MockManipulationEnv:
    """Deterministic mock environment for CI and early pipeline development.

    This is not a robot simulator. It exists so the logging, baseline, stressor,
    and reporting pipeline can be developed before binding to ManiSkill or Isaac.
    """

    def __init__(self, task: str, seed: int = 0):
        self.task = task
        self.seed = seed
        self.rng = make_rng(seed)
        self.oracle_target = np.array([0.00, 0.00, 0.35], dtype=float)

    def reset(self) -> Observation:
        h, w = 128, 128
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        rgb[..., 0] = 120
        rgb[..., 1] = 80
        rgb[..., 2] = 60
        depth = np.ones((h, w), dtype=np.float32) * 0.50

        # Synthetic object crop around the center.
        x1, y1, x2, y2 = 45, 42, 83, 82
        depth[y1:y2, x1:x2] = 0.35 + self.rng.normal(0.0, 0.002, size=(y2 - y1, x2 - x1))
        rgb[y1:y2, x1:x2] = np.array([220, 40, 40], dtype=np.uint8)

        intrinsics = np.array([[100.0, 0.0, w / 2], [0.0, 100.0, h / 2], [0.0, 0.0, 1.0]])
        extrinsics = np.eye(4)
        detections = [
            {
                "label": "red cube",
                "score": 0.95,
                "bbox_xyxy": [x1, y1, x2, y2],
            }
        ]
        metadata = {
            "oracle_target_3d": self.oracle_target.tolist(),
            "task": self.task,
        }
        return Observation(
            rgb=rgb,
            depth=depth,
            intrinsics=intrinsics,
            extrinsics=extrinsics,
            detections=detections,
            object_metadata=metadata,
        )

    def execute_pick(self, target_3d: np.ndarray | None, execution_offset: np.ndarray | None = None) -> ExecutionResult:
        if target_3d is None:
            return ExecutionResult(False, "no_target", {})
        target = np.asarray(target_3d, dtype=float)
        if execution_offset is not None:
            target = target + np.asarray(execution_offset, dtype=float)
        error = float(np.linalg.norm(target - self.oracle_target))
        threshold = 0.055
        success = error <= threshold
        return ExecutionResult(
            success=success,
            failure_type=None if success else "target_error_too_large",
            debug_info={"target_error_l2": error, "success_threshold": threshold},
        )
