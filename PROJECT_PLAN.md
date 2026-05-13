# EmbodiedStressBench Project Plan

## Goal

Build a publishable IEEE Access-style benchmark paper:

**EmbodiedStressBench: AI-Driven Stress Testing for Language-Conditioned Embodied Manipulation**

The first version should be a rigorous engineering/AI systems paper, not a top-conference SOTA claim.

## Research positioning

This project studies a practical bottleneck in embodied AI:

- Vision-language systems can often localize or describe objects.
- Manipulation pipelines need executable 3D targets.
- Clean success rates hide fragility under language ambiguity, RGB-D noise, occlusion, camera error, and execution perturbation.
- A stress-testing framework can reveal where and why pipelines fail.

## Minimum viable paper

The MVP paper needs:

1. A working benchmark framework.
2. A stressor taxonomy.
3. Several target-source baselines.
4. Structured failure taxonomy.
5. Large-scale simulation results.
6. Clear limitations: simulation-only, no real robot claims.

## Six-week plan

### Week 1: Starter repo and mock-to-sim transition

- Verify mock smoke test.
- Add ManiSkill adapter or reuse existing Query-to-Grasp wrappers.
- Run PickCube with oracle target for 5 seeds.
- Run PickCube with crop-depth baselines for 5 seeds.
- Confirm JSON schema and result logging.

Exit criterion:

```bash
python -m embodied_stressbench.runners.run_single --task PickCube --baseline crop_median_depth --seed 0 --output outputs/w1_smoke
```

### Week 2: Stressor implementation

- Implement depth noise.
- Implement occlusion.
- Implement execution offset.
- Implement semantic variants from config.
- Add camera pose noise if environment supports camera metadata.
- Run tiny matrix: 2 tasks × 3 baselines × 3 stressors × 3 levels × 10 seeds.

Exit criterion:

- At least 500 result JSON files.
- One markdown report generated from result files.

### Week 3: Benchmark expansion

- Add StackCube.
- Add PickSingleYCB or available non-cube task.
- Add PickClutterYCB if assets are available.
- Add crop_top_surface and multi-view memory baseline.
- Add failure taxonomy and oracle-gap metric.

Exit criterion:

- 3 tasks × 5 baselines × 4 stressors × 4 levels × 50 seeds.

### Week 4: H200 large-scale run

Recommended full matrix:

- Tasks: 3–4
- Baselines: 5
- Stressors: 5–6
- Levels: 4
- Seeds: 100–300

Expected total:

```text
3 × 5 × 5 × 4 × 200 = 60,000 runs
```

Run only after small matrix validates.

### Week 5: Analysis and first paper draft

Generate:

- clean success table;
- robustness curves;
- oracle-gap heatmap;
- failure distribution chart;
- qualitative failure gallery;
- limitations section;
- reproducibility appendix.

### Week 6: IEEE Access submission package

- Polish paper.
- Clean repository.
- Create reproducibility checklist.
- Verify no unsupported claims.
- Prepare cover letter.
- Decide whether to release code publicly before submission.

## Key deliverables

- Working codebase.
- Experiment configs.
- Result JSON/JSONL.
- Generated tables and figures.
- Paper draft.
- README and reproducibility commands.

## Red lines

- Do not fabricate results.
- Do not claim real-robot validation without real robot or real sensor data.
- Do not run a huge matrix before smoke tests pass.
- Do not let Codex silently change experiment definitions after results are generated.
- Do not mix unrelated results from different configs without recording provenance.
