from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from embodied_stressbench.types import Observation, TargetPrediction


class TargetSourceBaseline(ABC):
    name: str

    @abstractmethod
    def predict_target(self, observation: Observation, query: str, context: Dict[str, Any]) -> TargetPrediction:
        raise NotImplementedError
