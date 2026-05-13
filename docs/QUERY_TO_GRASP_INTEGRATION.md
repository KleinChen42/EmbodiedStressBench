# Query-to-Grasp Integration Notes

This starter project is stored under `projects/EmbodiedStressBench/` as a
standalone research direction. It should not modify frozen Query-to-Grasp RAS
results unless an experiment is explicitly promoted back into the main paper.

## Local setup

From the project directory:

```bash
cd projects/EmbodiedStressBench
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -e .
```

The package can also be run without installation when the current working
directory is `projects/EmbodiedStressBench`.

## Verified starter commands

```bash
python -m pytest -q

python -m embodied_stressbench.runners.run_single \
  --task PickCube \
  --baseline oracle_target \
  --seed 0 \
  --output outputs/smoke_pickcube_oracle

python -m embodied_stressbench.runners.run_matrix \
  --config configs/experiments/exp_tiny_mock.yaml \
  --output outputs/tiny_mock

python -m embodied_stressbench.reporting.make_report \
  --input outputs/tiny_mock \
  --output outputs/tiny_mock/report.md
```

## Relationship to Query-to-Grasp

- Query-to-Grasp remains the RAS target-source diagnostic framework.
- EmbodiedStressBench is a new benchmark direction for broader stress testing:
  semantic variants, visual occlusion, depth noise, camera pose noise, and
  execution perturbations.
- The first engineering milestone should be a ManiSkill adapter that reuses
  Query-to-Grasp target-source implementations where possible:
  `box_center_depth`, `crop_median`, `crop_top_surface`, `oracle_object_pose`,
  and later multi-view memory.
- Any future shared code should be moved deliberately into a common utility
  layer rather than copied silently between projects.

## Claim boundary

The starter currently runs in a mock environment. It does not yet provide
ManiSkill results, real-robot validation, or paper-ready benchmark evidence.
