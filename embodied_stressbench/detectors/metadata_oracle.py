from __future__ import annotations

from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.perception.detection_selection import select_detection
from embodied_stressbench.types import Observation


class MetadataOracleProvider:
    """Controlled query-aware selector over simulator-provided detections.

    This is not a deployed detector. It is a diagnostic upper/comparator that
    uses labels and metadata already present in the simulator observation.
    """

    name = "metadata_query_aware"

    def detect(self, observation: Observation, query: str) -> DetectionProviderResult:
        detection, debug = select_detection(observation, query)
        detections = [detection] if detection is not None else []
        debug["provider"] = self.name
        return DetectionProviderResult(detections=detections, debug_info=debug)
