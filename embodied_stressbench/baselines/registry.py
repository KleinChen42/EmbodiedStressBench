from __future__ import annotations

from embodied_stressbench.baselines.base import TargetSourceBaseline
from embodied_stressbench.baselines.multiview_memory import MultiViewMemoryBaseline
from embodied_stressbench.baselines.oracle_target import OracleTargetBaseline
from embodied_stressbench.baselines.rgbd_crop import (
    BoxCenterDepthBaseline,
    BoxCenterDepthClipRerankBaseline,
    BoxCenterDepthFirstDetectionBaseline,
    BoxCenterDepthGroundingDinoBaseline,
    BoxCenterDepthQueryAwareBaseline,
    CropMedianDepthBaseline,
    CropMedianDepthClipRerankBaseline,
    CropMedianDepthFirstDetectionBaseline,
    CropMedianDepthGroundingDinoBaseline,
    CropMedianDepthQueryAwareBaseline,
    CropTrimmedMedianDepthBaseline,
    CropTrimmedMedianDepthFirstDetectionBaseline,
    CropTrimmedMedianDepthGroundingDinoBaseline,
    CropTrimmedMedianDepthQueryAwareBaseline,
    CropTopSurfaceBaseline,
    CropTopSurfaceFirstDetectionBaseline,
    CropTopSurfaceQueryAwareBaseline,
)

_BASELINES = {
    "oracle_target": OracleTargetBaseline,
    "box_center_depth": BoxCenterDepthBaseline,
    "box_center_depth_query_aware": BoxCenterDepthQueryAwareBaseline,
    "box_center_depth_first_detection": BoxCenterDepthFirstDetectionBaseline,
    "box_center_depth_clip_rerank": BoxCenterDepthClipRerankBaseline,
    "box_center_depth_grounding_dino": BoxCenterDepthGroundingDinoBaseline,
    "crop_median_depth": CropMedianDepthBaseline,
    "crop_median_depth_query_aware": CropMedianDepthQueryAwareBaseline,
    "crop_median_depth_first_detection": CropMedianDepthFirstDetectionBaseline,
    "crop_median_depth_clip_rerank": CropMedianDepthClipRerankBaseline,
    "crop_median_depth_grounding_dino": CropMedianDepthGroundingDinoBaseline,
    "crop_trimmed_median_depth": CropTrimmedMedianDepthBaseline,
    "crop_trimmed_median_depth_query_aware": CropTrimmedMedianDepthQueryAwareBaseline,
    "crop_trimmed_median_depth_first_detection": CropTrimmedMedianDepthFirstDetectionBaseline,
    "crop_trimmed_median_depth_grounding_dino": CropTrimmedMedianDepthGroundingDinoBaseline,
    "crop_top_surface": CropTopSurfaceBaseline,
    "crop_top_surface_query_aware": CropTopSurfaceQueryAwareBaseline,
    "crop_top_surface_first_detection": CropTopSurfaceFirstDetectionBaseline,
    "multiview_memory": MultiViewMemoryBaseline,
}


def get_baseline(name: str) -> TargetSourceBaseline:
    try:
        return _BASELINES[name]()
    except KeyError as e:
        raise ValueError(f"Unknown baseline: {name}. Available: {sorted(_BASELINES)}") from e
