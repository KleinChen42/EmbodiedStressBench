from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import numpy as np

from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.types import Observation


@dataclass
class ClipRerankProvider:
    """Optional CLIP crop reranker over existing candidate detections.

    This provider does not create boxes. It reranks simulator or detector
    candidate boxes using image-text similarity. The dependency stack is
    intentionally optional; if `transformers`, `torch`, or `PIL` are missing,
    construction raises an actionable ImportError instead of silently producing
    fake results.
    """

    model_name: str | None = None
    device: str | None = None
    name: str = "clip_rerank"

    def __post_init__(self) -> None:
        if self.model_name is None:
            self.model_name = os.environ.get("EMBODIED_STRESSBENCH_CLIP_MODEL", "openai/clip-vit-base-patch32")
        local_files_only = os.environ.get("EMBODIED_STRESSBENCH_CLIP_LOCAL_FILES_ONLY", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        try:
            import torch
            from PIL import Image
            from transformers import CLIPModel, CLIPProcessor
        except ImportError as exc:
            raise ImportError(
                "ClipRerankProvider requires optional dependencies: "
                "torch, pillow, and transformers. Install them and make sure "
                "the CLIP model is available locally or downloadable."
            ) from exc
        self._torch = torch
        self._image_cls = Image
        self._processor = CLIPProcessor.from_pretrained(self.model_name, local_files_only=local_files_only)
        self._model = CLIPModel.from_pretrained(self.model_name, local_files_only=local_files_only)
        if self.device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model.to(self.device)
        self._model.eval()

    def detect(self, observation: Observation, query: str) -> DetectionProviderResult:
        if observation.rgb is None or not observation.detections:
            return DetectionProviderResult([], {"reason": "missing_rgb_or_detections", "provider": self.name})
        crops: list[Any] = []
        valid_detections: list[dict[str, Any]] = []
        h, w = observation.rgb.shape[:2]
        for det in observation.detections:
            bbox = det.get("bbox_xyxy")
            if bbox is None:
                continue
            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1 = max(0, min(w - 1, x1))
            x2 = max(x1 + 1, min(w, x2))
            y1 = max(0, min(h - 1, y1))
            y2 = max(y1 + 1, min(h, y2))
            crop = observation.rgb[y1:y2, x1:x2]
            crops.append(self._image_cls.fromarray(np.asarray(crop, dtype=np.uint8)))
            valid_detections.append(dict(det))
        if not crops:
            return DetectionProviderResult([], {"reason": "no_valid_crops", "provider": self.name})

        inputs = self._processor(text=[query], images=crops, return_tensors="pt", padding=True).to(self.device)
        with self._torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits_per_image[:, 0]
            scores = logits.detach().cpu().numpy()
        order = list(np.argsort(-scores))
        reranked = []
        for idx in order:
            det = dict(valid_detections[int(idx)])
            det["clip_score"] = float(scores[int(idx)])
            reranked.append(det)
        return DetectionProviderResult(
            detections=reranked,
            debug_info={"provider": self.name, "model_name": self.model_name, "num_candidates": len(reranked)},
        )
