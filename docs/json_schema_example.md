# Episode JSON Schema Example

Machine-readable schema:

- `schemas/episode_result_schema.json`

Example episode result:

```json
{
  "status": "ok",
  "task": "PickCube",
  "backend": "maniskill",
  "seed": 0,
  "baseline": "crop_median_depth",
  "query_original": "pick the red cube",
  "query_used": "pick the red cube",
  "stressor": "depth_sparsity",
  "level": 2,
  "stress_info": {
    "name": "depth_sparsity",
    "level": 2,
    "params": {
      "missing_prob": 0.5,
      "target_bbox_xyxy": [10, 20, 40, 60]
    }
  },
  "success": true,
  "failure_type": "success",
  "prediction": {
    "target_3d": [0.01, 0.02, 0.35],
    "confidence": 1.0,
    "debug_info": {}
  },
  "execution_debug": {
    "target_error_l2": 0.02,
    "success_threshold": 0.08,
    "diagnostic_execution": true
  },
  "target_error_l2": 0.02,
  "num_detections": 1,
  "runtime_sec": 0.4
}
```

Notes:

- `target_error_l2` is the predicted target error before any execution offset
  unless the backend also records an execution-adjusted error in
  `execution_debug.target_error_l2`.
- Threshold sensitivity uses `execution_debug.target_error_l2` when available.
- `failure_type` is `success`, `wrong_detection_selected`,
  `target_error_too_large`, `depth_invalid`, or another explicitly logged
  runner/backend failure.
