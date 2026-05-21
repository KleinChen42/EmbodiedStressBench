from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from embodied_stressbench.types import Observation


@dataclass(frozen=True)
class DetectionProviderResult:
    detections: list[dict[str, Any]]
    debug_info: dict[str, Any]


class DetectionProvider(Protocol):
    """Interface for pluggable language-conditioned detection providers."""

    name: str

    def detect(self, observation: Observation, query: str) -> DetectionProviderResult:
        """Return detections ordered by provider confidence for the query."""
