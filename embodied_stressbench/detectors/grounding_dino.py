from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import numpy as np

from embodied_stressbench.detectors.base import DetectionProviderResult
from embodied_stressbench.types import Observation


def _iou_xyxy(a: list[float] | None, b: list[float] | None) -> float:
    if a is None or b is None:
        return 0.0
    ax1, ay1, ax2, ay2 = [float(v) for v in a]
    bx1, by1, bx2, by2 = [float(v) for v in b]
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix1)
    ih = max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


@dataclass
class GroundingDinoProvider:
    """GroundingDINO zero-shot detector plug-in.

    This is an optional bridge baseline for IEEE Access. It uses a learned
    open-vocabulary detector to propose boxes from RGB, then hands the top box
    to the same RGB-D target-source code used by the metadata baselines.
    """

    model_name: str | None = None
    device: str | None = None
    box_threshold: float = 0.20
    text_threshold: float = 0.20
    name = "grounding_dino"

    def __post_init__(self) -> None:
        if self.model_name is None:
            self.model_name = os.environ.get("EMBODIED_STRESSBENCH_GDINO_MODEL", "IDEA-Research/grounding-dino-tiny")
        self.box_threshold = float(os.environ.get("EMBODIED_STRESSBENCH_GDINO_BOX_THRESHOLD", self.box_threshold))
        self.text_threshold = float(os.environ.get("EMBODIED_STRESSBENCH_GDINO_TEXT_THRESHOLD", self.text_threshold))
        local_files_only = os.environ.get("EMBODIED_STRESSBENCH_GDINO_LOCAL_FILES_ONLY", "1").lower() in {
            "1",
            "true",
            "yes",
        }
        try:
            import torch
            from PIL import Image
            from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor
        except ImportError as exc:
            raise ImportError(
                "GroundingDinoProvider requires optional dependencies: torch, pillow, and transformers. "
                f"Original import error: {exc!r}"
            ) from exc
        self._torch = torch
        self._image_cls = Image
        self._processor = AutoProcessor.from_pretrained(self.model_name, local_files_only=local_files_only)
        self._model = AutoModelForZeroShotObjectDetection.from_pretrained(
            self.model_name,
            local_files_only=local_files_only,
        )
        if self.device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model.to(self.device)
        self._model.eval()

    def detect(self, observation: Observation, query: str) -> DetectionProviderResult:
        if observation.rgb is None:
            return DetectionProviderResult([], {"provider": self.name, "reason": "missing_rgb"})
        image = self._image_cls.fromarray(np.asarray(observation.rgb, dtype=np.uint8))
        text = query.strip()
        if not text.endswith("."):
            text = f"{text}."
        inputs = self._processor(images=image, text=text, return_tensors="pt").to(self.device)
        with self._torch.no_grad():
            outputs = self._model(**inputs)

        target_sizes = self._torch.tensor([image.size[::-1]], device=self.device)
        if hasattr(self._processor, "post_process_grounded_object_detection"):
            try:
                processed = self._processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    box_threshold=self.box_threshold,
                    text_threshold=self.text_threshold,
                    target_sizes=target_sizes,
                )
            except TypeError:
                processed = self._processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    threshold=self.box_threshold,
                    text_threshold=self.text_threshold,
                    target_sizes=target_sizes,
                )
        else:
            processed = self._processor.post_process_object_detection(
                outputs,
                threshold=self.box_threshold,
                target_sizes=target_sizes,
            )
        if not processed:
            return DetectionProviderResult([], {"provider": self.name, "reason": "no_postprocess_result"})

        result = processed[0]
        boxes = result.get("boxes", [])
        scores = result.get("scores", [])
        labels = result.get("labels", result.get("text_labels", []))
        target_bbox = observation.object_metadata.get("target_bbox_xyxy")
        detections: list[dict[str, Any]] = []
        for idx, box in enumerate(boxes):
            bbox = [float(v) for v in box.detach().cpu().tolist()]
            label = labels[idx] if idx < len(labels) else query
            if not isinstance(label, str):
                label = str(label)
            score = float(scores[idx].detach().cpu().item()) if idx < len(scores) else 0.0
            iou = _iou_xyxy(bbox, target_bbox)
            detections.append(
                {
                    "label": label,
                    "score": score,
                    "bbox_xyxy": bbox,
                    "source": self.name,
                    "is_target": bool(iou >= 0.25),
                    "distractor_type": None if iou >= 0.25 else "open_vocab_non_target",
                    "query_aliases": [query],
                    "target_iou": iou,
                }
            )
        detections.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        return DetectionProviderResult(
            detections=detections,
            debug_info={
                "provider": self.name,
                "model_name": self.model_name,
                "num_detections": len(detections),
                "box_threshold": self.box_threshold,
                "text_threshold": self.text_threshold,
            },
        )
