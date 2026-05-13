# Codex Master Prompt

You are an expert research engineer in embodied AI, robot learning, RGB-D perception, and simulation-based benchmarking.

We are building a new research project called EmbodiedStressBench.

## Goal

Create a publishable simulation-based benchmark and diagnostic framework for stress-testing language-conditioned embodied manipulation pipelines. The project should not require a real robot. It should use simulation and reproducible offline experiments. The target paper is an engineering AI / robotics journal paper, not a top-conference SOTA claim.

## Core thesis

Current language-conditioned manipulation pipelines are often evaluated under clean settings. We want to stress-test them under semantic, visual, geometric, and execution perturbations, and diagnose whether failures come from semantic retrieval, RGB-D target generation, multi-view association, or execution fragility.

## Constraints

- No real robot hardware.
- Use Python.
- Prefer ManiSkill or existing simulation wrappers.
- Keep the architecture modular and reproducible.
- Every run must save machine-readable JSON metrics.
- Never hardcode fake results.
- Every figure and table must be generated from saved results.
- Start with a minimal working system before scaling.
- Code should be clean, testable, and suitable for open-source release.
- The system should support large-scale execution on an 8×H200 server.

## Initial MVP

Tasks:

1. PickCube
2. StackCube
3. PickSingleYCB
4. PickClutterYCB

Baselines:

1. oracle_target
2. box_center_depth
3. crop_median_depth
4. crop_top_surface
5. multiview_memory

Stressors:

1. semantic ambiguity
2. visual occlusion
3. depth noise
4. camera pose noise
5. object distractors
6. execution target offset

Metrics:

1. success rate
2. target 3D error
3. valid depth ratio
4. oracle gap
5. failure type
6. runtime
7. robustness curve across perturbation levels

## Your first task

1. Inspect the current repository if one exists.
2. Propose a concrete implementation plan.
3. Create the repository skeleton.
4. Implement the minimal configuration system.
5. Implement a smoke-test runner that can run one task, one baseline, one seed, and save a JSON result.
6. Add a README with exact commands.
7. Do not implement large-scale experiments until the smoke test passes.

## Important

After every change, run the smallest possible test.
If an environment dependency is missing, write a graceful fallback or a clear installation note.
Do not invent experimental results.
Do not write paper claims that are not supported by JSON outputs.
