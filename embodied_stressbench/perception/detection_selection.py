from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from embodied_stressbench.types import Observation


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def select_detection(observation: Observation, query: str) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    """Select one detection using a deterministic, lightweight query match.

    This is deliberately not a VLM or open-vocabulary detector. It only ranks
    existing simulator/detection metadata, which keeps Main v1 focused on
    target-source diagnostics rather than learned grounding quality.
    """
    if not observation.detections:
        return None, {"selection_failure_reason": "no_detection"}

    query_tokens = _tokens(query)
    scored = []
    for index, detection in enumerate(observation.detections):
        fields = [
            str(detection.get("label", "")),
            " ".join(str(v) for v in detection.get("query_aliases", [])),
            str(detection.get("color", "")),
            str(detection.get("shape", "")),
        ]
        det_tokens = set()
        for field in fields:
            det_tokens |= _tokens(field)
        overlap = query_tokens & det_tokens
        lexical_score = float(len(overlap))
        metadata_score = 0.25 if detection.get("is_target") and {"target", "requested"} & query_tokens else 0.0
        confidence_score = 0.01 * float(detection.get("score", 0.0))
        score = lexical_score + metadata_score + confidence_score
        match_score = lexical_score + metadata_score
        scored.append((score, match_score, -index, index, detection, sorted(overlap)))

    score, match_score, _, index, detection, overlap = max(scored, key=lambda item: (item[0], item[1], item[2]))
    if match_score <= 0.0:
        detection = observation.detections[0]
        index = 0
        overlap = []
        reason = "no_query_match_fallback_first_detection"
    else:
        reason = None

    return detection, {
        "selected_detection_index": int(index),
        "selected_detection_label": detection.get("label"),
        "selected_detection_is_target": bool(detection.get("is_target", False)),
        "selected_detection_distractor_type": detection.get("distractor_type"),
        "query_overlap_tokens": overlap,
        "selection_failure_reason": reason,
        "num_candidate_detections": len(observation.detections),
    }


def select_first_detection(observation: Observation, query: str) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    """Select the first detection without query-aware ranking.

    This baseline intentionally mirrors detectors or target-source pipelines
    that consume the top-ranked detection directly. It is useful as a control
    for measuring whether distractor stressors create real target-selection
    pressure.
    """
    if not observation.detections:
        return None, {"selection_failure_reason": "no_detection"}
    detection = observation.detections[0]
    return detection, {
        "selected_detection_index": 0,
        "selected_detection_label": detection.get("label"),
        "selected_detection_is_target": bool(detection.get("is_target", False)),
        "selected_detection_distractor_type": detection.get("distractor_type"),
        "query_overlap_tokens": [],
        "selection_failure_reason": None,
        "num_candidate_detections": len(observation.detections),
        "selection_strategy": "first_detection",
    }
