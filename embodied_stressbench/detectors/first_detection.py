from __future__ import annotations

from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.perception.detection_selection import select_first_detection
from embodied_stressbench.types import Observation


class FirstDetectionProvider:
    """Stress-sensitive lower comparator that returns the first detection."""

    name = "first_detection"

    def detect(self, observation: Observation, query: str) -> DetectionProviderResult:
        detection, debug = select_first_detection(observation, query)
        detections = [detection] if detection is not None else []
        debug["provider"] = self.name
        return DetectionProviderResult(detections=detections, debug_info=debug)
