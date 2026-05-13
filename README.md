# EmbodiedStressBench

**AI-Driven Stress Testing for Language-Conditioned Embodied Manipulation**

EmbodiedStressBench is a starter research codebase for building a publishable simulation-based benchmark and diagnostic framework. The project is designed for a setting with strong GPU compute, AI coding assistance, and no real robot hardware.

Target paper direction:

> EmbodiedStressBench: AI-Driven Stress Testing for Language-Conditioned Embodied Manipulation

Target venue for the first version:

> IEEE Access / intelligent robotics / engineering AI style journal

Core thesis:

> Current language-conditioned manipulation pipelines are often evaluated under clean success-rate settings. EmbodiedStressBench stress-tests these pipelines under semantic, visual, geometric, and execution perturbations, and diagnoses whether failures come from semantic retrieval, RGB-D target generation, multi-view association, or execution fragility.

## What this starter includes

- A reproducible Python package skeleton.
- Config-driven experiment definitions.
- A mock manipulation environment that runs without ManiSkill or robot hardware.
- Baseline target-source methods:
  - `oracle_target`
  - `box_center_depth`
  - `crop_median_depth`
  - `crop_top_surface`
  - `multiview_memory` placeholder
- Stressors:
  - semantic query variants
  - depth noise
  - visual occlusion
  - camera pose noise placeholder
  - execution target offset
- JSON/JSONL result logging.
- Batch runner with resume and error recording.
- Report aggregation scripts.
- Codex prompts for incremental development.
- A 6-week project plan.
- Paper skeleton in LaTeX.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

Run the mock smoke test:

```bash
python -m embodied_stressbench.runners.run_single \
  --task PickCube \
  --baseline oracle_target \
  --seed 0 \
  --output outputs/smoke_pickcube_oracle
```

Run a tiny experiment matrix:

```bash
python -m embodied_stressbench.runners.run_matrix \
  --config configs/experiments/exp_tiny_mock.yaml \
  --output outputs/tiny_mock
```

Generate a markdown report:

```bash
python -m embodied_stressbench.reporting.make_report \
  --input outputs/tiny_mock \
  --output outputs/tiny_mock/report.md
```

## Design principles

1. **No fake results.** Every table and figure must come from JSON/JSONL outputs.
2. **Simulation-first.** The starter runs in mock mode; ManiSkill/Isaac/LIBERO adapters can be added later.
3. **Small-to-large scaling.** Run 1 seed → 5 seeds → 20 seeds → 100 seeds → full matrix.
4. **Failure is data.** Crashes and failed episodes are recorded as structured results.
5. **Codex-friendly.** Every module has simple interfaces and TODO blocks.
6. **Paper-first engineering.** The code produces the artifacts needed for a journal paper.

## Recommended first milestone

In the first 48 hours, aim to complete:

- mock smoke test passing;
- tiny matrix passing;
- report generated from result files;
- README commands verified;
- project pushed to GitHub;
- Codex assigned to replace mock environment with ManiSkill wrapper.

## Suggested paper contribution claims

Use only after supported by actual experiments:

1. A modular stress-testing framework for language-conditioned manipulation pipelines.
2. A four-part perturbation taxonomy: semantic, visual, geometric, and execution stressors.
3. A unified failure taxonomy and oracle-gap analysis for executable 3D targets.
4. Large-scale evidence that clean-setting success rates can hide severe fragility under RGB-D and execution perturbations.

## Safety and ethics

This project does not claim real-robot validation unless real-robot or real-sensor experiments are actually performed. It is explicitly positioned as a simulation-based diagnostic benchmark.
