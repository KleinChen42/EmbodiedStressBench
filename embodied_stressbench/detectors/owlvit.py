from __future__ import annotations

from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.types import Observation


class OwlVitProvider:
    """Placeholder interface for a future OWL-ViT detector plug-in."""

    name = "owlvit"

    def __init__(self, *_, **__) -> None:
        raise NotImplementedError(
            "OWL-ViT is not bundled with this repository. Use this class as "
            "the integration point after installing a Transformers OWL-ViT model."
        )

    def detect(self, observation: Observation, query: str) -> DetectionProviderResult:
        raise NotImplementedError
