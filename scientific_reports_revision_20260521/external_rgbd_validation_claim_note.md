# External RGB-D Validation Claim Note

Input artifact: `outputs/ycbv_external_rgbd_probe_160k_20260522_analysis`

## Supported claim

The YCB-V/BOP probe provides external real RGB-D evidence that EmbodiedStressBench
can separate RGB-D target lifting from detector/query failure. The visible-mask
oracle reaches 99.97% success at 8 cm, while
oracle 2D boxes with crop-trimmed median depth reach 79.9%.
GroundingDINO with generic prompts reaches only 23.8%
with crop-trimmed median lifting, but true-name prompts recover to
61.4% on the same real RGB-D probe.

## Boundary

This is not a real-robot manipulation result and does not compare detector
leaderboards. It is an external RGB-D target-generation probe using YCB-V/BOP
ground-truth visible masks/boxes as references and controls.
