from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class Observation:
    rgb: Optional[np.ndarray]
    depth: Optional[np.ndarray]
    intrinsics: Optional[np.ndarray]
    extrinsics: Optional[np.ndarray]
    detections: List[Dict[str, Any]] = field(default_factory=list)
    object_metadata: Dict[str, Any] = field(default_factory=dict)
    debug_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TargetPrediction:
    target_3d: Optional[np.ndarray]
    confidence: float
    debug_info: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None

    def to_jsonable(self) -> Dict[str, Any]:
        return {
            "target_3d": None if self.target_3d is None else [float(x) for x in self.target_3d],
            "confidence": float(self.confidence),
            "debug_info": self.debug_info,
            "failure_reason": self.failure_reason,
        }
