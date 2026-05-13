from __future__ import annotations

from typing import Any, Dict

import numpy as np

from embodied_stressbench.baselines.base import TargetSourceBaseline
from embodied_stressbench.types import Observation, TargetPrediction


class OracleTargetBaseline(TargetSourceBaseline):
    name = "oracle_target"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        target = observation.object_metadata.get("oracle_target_3d")
        if target is None:
            return TargetPrediction(None, 0.0, {}, "missing_oracle_target")
        return TargetPrediction(
            target_3d=np.asarray(target, dtype=float),
            confidence=1.0,
            debug_info={"source": "object_metadata.oracle_target_3d"},
        )
