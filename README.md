# EmbodiedStressBench

**A reproducible diagnostic benchmark for stress testing language-to-target generation in robotic manipulation**

EmbodiedStressBench is a simulation-based diagnostic benchmark for isolating
failures in the language-query-to-3D-target stage of robotic manipulation
pipelines. It evaluates how target selection, RGB-D target generation, visual
and geometric corruptions, semantic distractors, and execution perturbations
affect diagnostic manipulation success.

Current IEEE Access manuscript title:

> EmbodiedStressBench: A Reproducible Diagnostic Benchmark for Stress Testing Language-to-Target Generation in Robotic Manipulation

Target venue for the first version:

> IEEE Access / intelligent robotics / engineering AI style journal

Core thesis:

> Clean manipulation success can hide failures in the target-generation stage.
> EmbodiedStressBench stress-tests this stage under semantic, visual,
> geometric, and execution perturbations, then separates semantic selection,
> RGB-D target generation, depth validity, and execution-tolerance failures
> using oracle-gap and failure-taxonomy analyses.

## IEEE Access Manuscript Source

The canonical submission source is:

```text
paper/ieee_access/main_revised.tex
```

Do not compile `paper/main.tex` for submission. It is a legacy guard that
intentionally errors to prevent accidentally rebuilding the old experiment-log
draft. To build the submission PDF when a LaTeX environment is available, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_ieee_access_pdf.ps1
```

Generated main-text tables live in `paper/ieee_access/tables/`. Oversized
generated tables are moved to `paper/ieee_access/tables/supplement/` and can be
compiled through `paper/ieee_access/supplementary_tables.tex`.
The IEEE Access directory also includes `paper/ieee_access/references.bib`, so
BibTeX should use `\bibliography{references}` from that manuscript directory.

## What this repository includes

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
- IEEE Access manuscript source and generated analysis artifacts.

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

## H200 helper scripts

This project includes self-contained H200 connection helpers under `scripts/`.
They use the SSH key named `hd03-tenant13-research-20260405` from
`$HOME/.ssh/` and read the key passphrase from either the current environment
or a local `.env.local` file. Do not commit `.env.local`.

Create a local secret file if desired:

```powershell
Copy-Item .env.local.example .env.local
# edit .env.local and set SSH_KEY_PASSPHRASE
```

Check H200 status:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\h200_status.ps1
```

Run a read-only remote command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\invoke_h200_command.ps1 `
  -RemoteCommand "date && pwd && nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader"
```

Launch a remote script without blocking the local PowerShell session:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\h200_launch_detached.ps1 `
  -RemoteScript outputs/my_launch.sh `
  -RemoteDir /home/zetyun/OpenMythos_test
```

Sync lightweight files:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_h200_files.ps1 `
  -Direction push `
  -Paths configs\experiments\exp_tiny_mock.yaml
```

## Design principles

1. **No fake results.** Every table and figure must come from JSON/JSONL outputs.
2. **Simulation-first.** The starter runs in mock mode; ManiSkill/Isaac/LIBERO adapters can be added later.
3. **Small-to-large scaling.** Run 1 seed -> 5 seeds -> 20 seeds -> 100 seeds -> full matrix.
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
