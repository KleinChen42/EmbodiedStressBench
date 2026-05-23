# YCB-V Detector-Threshold Sensitivity Note

The full YCB-V/BOP external RGB-D probe was repeated for three GroundingDINO box/text threshold settings.

| Threshold | Generic | Photo true-name | True-name |
| --- | ---: | ---: | ---: |
| 0.10/0.10 | 23.8 | 46.0 | 61.5 |
| 0.20/0.20 | 23.8 | 46.0 | 61.4 |
| 0.30/0.25 | 23.8 | 44.2 | 60.0 |

Interpretation: true-name prompts remain far above the generic prompt across detector-threshold settings. The stricter 0.30/0.25 setting slightly reduces true-name success and increases no-detection, but does not change the qualitative conclusion.