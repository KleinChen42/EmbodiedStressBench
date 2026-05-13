from __future__ import annotations

from typing import Any, Dict

from embodied_stressbench.baselines.rgbd_crop import CropMedianDepthBaseline
from embodied_stressbench.types import Observation, TargetPrediction


class MultiViewMemoryBaseline(CropMedianDepthBaseline):
    """Placeholder baseline.

    In the starter, this falls back to crop median depth while recording that a
    true multi-view memory module is not yet implemented. Replace this with the
    Query-to-Grasp memory module when available.
    """

    name = "multiview_memory"

    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        pred = super().predict_target(observation, query, context)
        pred.debug_info["placeholder"] = "multiview_memory currently falls back to crop_median_depth"
        pred.confidence = min(pred.confidence, 0.62)
        return pred
