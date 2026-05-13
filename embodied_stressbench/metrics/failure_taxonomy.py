from __future__ import annotations


def classify_failure(prediction_failure: str | None, execution_failure: str | None) -> str | None:
    if prediction_failure:
        if "no_detection" in prediction_failure:
            return "no_detection"
        if "depth" in prediction_failure:
            return "depth_invalid"
        if "oracle" in prediction_failure:
            return "missing_oracle"
        return "target_prediction_failure"
    if execution_failure:
        return execution_failure
    return None
