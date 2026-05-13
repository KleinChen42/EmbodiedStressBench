from __future__ import annotations

from embodied_stressbench.baselines.base import TargetSourceBaseline
from embodied_stressbench.baselines.multiview_memory import MultiViewMemoryBaseline
from embodied_stressbench.baselines.oracle_target import OracleTargetBaseline
from embodied_stressbench.baselines.rgbd_crop import (
    BoxCenterDepthBaseline,
    CropMedianDepthBaseline,
    CropTopSurfaceBaseline,
)

_BASELINES = {
    "oracle_target": OracleTargetBaseline,
    "box_center_depth": BoxCenterDepthBaseline,
    "crop_median_depth": CropMedianDepthBaseline,
    "crop_top_surface": CropTopSurfaceBaseline,
    "multiview_memory": MultiViewMemoryBaseline,
}


def get_baseline(name: str) -> TargetSourceBaseline:
    try:
        return _BASELINES[name]()
    except KeyError as e:
        raise ValueError(f"Unknown baseline: {name}. Available: {sorted(_BASELINES)}") from e
