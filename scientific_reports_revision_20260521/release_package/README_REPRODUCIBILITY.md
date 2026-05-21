# EmbodiedStressBench Reproducibility Pack

This document describes how to reproduce the IEEE Access revision artifacts for
EmbodiedStressBench.

## Repository Structure

- `embodied_stressbench/`: benchmark code
- `configs/experiments/`: experiment matrices
- `configs/stressors/`: parameterized stressor definitions
- `scripts/`: launch, report, statistics, figure, and table scripts
- `paper/ieee_access/`: revised IEEE Access manuscript source
- `paper/ieee_access/tables/`: generated LaTeX tables
- `paper/ieee_access/figures/`: generated figures
- `ieee_access_revision_20260520/`: generated CSV analysis outputs
- `schemas/`: JSON schema documentation

## Canonical IEEE Access Source

The submission manuscript must be compiled from:

```bash
paper/ieee_access/main_revised.tex
```

Do not compile `paper/main.tex`; it is a legacy guard that intentionally errors
to prevent old experiment-log drafts from being submitted.

The IEEE Access manuscript directory is self-contained for BibTeX. It includes
`paper/ieee_access/references.bib`, and `main_revised.tex` uses
`\bibliography{references}` so upload builds do not depend on parent-directory
paths.

To build or record the local build status:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_ieee_access_pdf.ps1
```

The script uses `latexmk` or `pdflatex` when available. If no LaTeX toolchain is
available, it writes `ieee_access_revision_20260520/pdf_build_status.md` with
the missing tools and next command to run.

## Environment

The H200 runs used:

- Python: `/home/zetyun/q2g_venv/bin/python`
- Backend: ManiSkill through `gymnasium`
- Output filesystem: `/data/openMythosBench_project/outputs`

Local analysis requires:

```bash
python -m pip install pandas numpy matplotlib pyyaml pytest
```

ManiSkill reproduction requires the H200 environment or an equivalent local
CUDA/SAPIEN/ManiSkill installation.

## Smoke Test

```bash
python -m pytest -q tests
python scripts/generate_stressor_table.py
python scripts/generate_paper_diagrams.py
```

## Main Experiment Configs and Expected Episodes

| Config | Expected episodes |
| --- | ---: |
| `configs/experiments/main_v1_ieee_access.yaml` | 44,800 |
| `configs/experiments/main_v1_ieee_access_confirmatory.yaml` | 22,400 |
| `configs/experiments/main_v1_ieee_access_hard_l3_extension.yaml` | 19,200 |
| `configs/experiments/weekend_main_v1_seed350_650.yaml` | 134,400 |
| `configs/experiments/weekend_visual_sensor_bridge_seed350_500.yaml` | 38,400 |
| `configs/experiments/weekend_hard_l3_seed650_800.yaml` | 14,400 |
| `configs/experiments/semantic_distractor_validity_v1.yaml` | 156,800 |
| `configs/experiments/open_vocab_grounding_dino_smoke.yaml` | 100 |
| `configs/experiments/open_vocab_grounding_dino_ieee_access_small.yaml` | 1,200 |
| `configs/experiments/open_vocab_grounding_dino_ieee_access_small_dino_first.yaml` | 1,200 |
| `configs/experiments/open_vocab_bridge_v2_smoke.yaml` | 144 |
| `configs/experiments/open_vocab_bridge_v2.yaml` | 13,500 |
| `configs/experiments/closed_loop_sanity_smoke.yaml` | 80 |
| `configs/experiments/closed_loop_sanity_subset.yaml` | 4,800 |
| `configs/experiments/open_vocab_smoke.yaml` | 480 |
| `configs/experiments/open_vocab_ieee_access_small.yaml` | 5,760 |

## Seed Splits

- Main v1 primary: seeds 0--99
- Confirmatory: 50 held-out seeds
- Held-out extension: seeds 350--649
- Hard L3 confirmation: seeds 650--799
- Semantic distractor validity: seeds 800--999
- GroundingDINO bridge smoke: seeds 0--4
- GroundingDINO bridge small: seeds 0--19
- Open-Vocab Bridge v2: seeds 0--29
- Closed-loop sanity subset: seeds 0--49

## Regenerate Reports

For each output root:

```bash
/home/zetyun/q2g_venv/bin/python -m embodied_stressbench.reporting.make_report \
  --input <OUTPUT_ROOT> \
  --output <OUTPUT_ROOT>/report.md
```

This creates:

- `success_by_group.csv`
- `oracle_gap_by_group.csv`
- `report.md`

## Regenerate IEEE Access Tables

```bash
/home/zetyun/q2g_venv/bin/python scripts/analyze_ieee_access_statistics.py \
  --run Primary=/data/openMythosBench_project/outputs/main_v1_ieee_access_20260514_full \
  --run Heldout=/data/openMythosBench_project/outputs/weekend_main_v1_seed350_650_20260516 \
  --run VisualBridge=/data/openMythosBench_project/outputs/weekend_visual_sensor_bridge_seed350_500_20260516 \
  --run HardL3Confirm=/data/openMythosBench_project/outputs/weekend_hard_l3_seed650_800_20260516 \
  --run Semantic=/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518 \
  --output-dir ieee_access_revision_20260520 \
  --tables-dir paper/ieee_access/tables \
  --bootstrap 1000
```

```bash
python scripts/generate_stressor_table.py
```

## Regenerate Threshold Sensitivity

```bash
/home/zetyun/q2g_venv/bin/python scripts/analyze_threshold_sensitivity.py \
  --run Primary=/data/openMythosBench_project/outputs/main_v1_ieee_access_20260514_full \
  --run Heldout=/data/openMythosBench_project/outputs/weekend_main_v1_seed350_650_20260516 \
  --run Semantic=/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518 \
  --output-dir ieee_access_revision_20260520 \
  --tables-dir paper/ieee_access/tables \
  --figures-dir paper/ieee_access/figures
```

Render publication-readable LaTeX tables from the generated CSV artifacts:

```bash
python scripts/render_ieee_access_tables_from_csv.py \
  --input-dir ieee_access_revision_20260520 \
  --tables-dir paper/ieee_access/tables
```

This produces compact main-text tables in `paper/ieee_access/tables/` and long
supplementary tables in `paper/ieee_access/tables/supplement/`. The separate
supplement entry is `paper/ieee_access/supplementary_tables.tex`.

## Regenerate Figures

```bash
python scripts/generate_ieee_access_ci_figures.py
python scripts/generate_paper_diagrams.py
python scripts/generate_benchmark_comparison_table.py
```

Historical generated figures can be regenerated with:

```bash
python scripts/generate_paper_figures.py --help
```

The qualitative/failure teaser is generated from JSON debug fields and writes a
case manifest for auditability:

```bash
/home/zetyun/q2g_venv/bin/python scripts/generate_ieee_access_qualitative_figures.py \
  --roots Main=/data/openMythosBench_project/outputs/main_v1_ieee_access_20260514_full \
          Semantic=/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518 \
          BridgeV2=/data/openMythosBench_project/outputs/open_vocab_bridge_v2_20260520 \
  --output-dir ieee_access_revision_20260520/qualitative \
  --figures-dir paper/ieee_access/figures
```

This creates:

- `paper/ieee_access/figures/qualitative_failure_teaser.pdf`
- `paper/ieee_access/figures/qualitative_failure_teaser.png`
- `ieee_access_revision_20260520/qualitative/qualitative_case_manifest.csv`

## Optional Open-Vocabulary Detector Bridge

GroundingDINO is the preferred learned detector bridge when its model cache is
available in the target environment. The final valid IEEE Access bridge used the
dino-first config and output root below:

- Config: `configs/experiments/open_vocab_grounding_dino_ieee_access_small_dino_first.yaml`
- Output: `/data/openMythosBench_project/outputs/open_vocab_grounding_dino_ieee_access_small_20260520_dino_first9`
- Episodes: 1,200 / 1,200
- Duplicate result filenames: 0
- No-detection failures: 0
- Runner exceptions: 0

Check model-cache availability first:

```bash
/home/zetyun/q2g_venv/bin/python scripts/check_open_vocab_model_cache.py
```

The reusable queue script uses GPU1--3, runs the 100-episode smoke first, checks
for zero runner exceptions, and then launches the 1,200-episode small
proof-of-concept. If the environment has shown late-import static TLS failures,
prefer the dino-first config so GroundingDINO loads before long metadata-only
phases:

```bash
DATE_TAG=20260520 bash scripts/run_h200_open_vocab_grounding_dino_queue.sh
```

Generate detector-bridge tables with:

```bash
/home/zetyun/q2g_venv/bin/python scripts/analyze_open_vocab_detector_bridge.py \
  --input /data/openMythosBench_project/outputs/open_vocab_grounding_dino_ieee_access_small_20260520_dino_first9 \
  --output-dir ieee_access_revision_20260520/open_vocab_detector_bridge_dino_first9 \
  --tables-dir paper/ieee_access/tables/open_vocab_detector_bridge_dino_first9
```

CLIP crop reranking is implemented, but it requires a local CLIP model cache or
network access to download `openai/clip-vit-base-patch32`. If the cache is
missing, CLIP episodes are explicitly marked `clip_rerank_unavailable` and
must not be reported as learned detector results.

Do not use the earlier non-dino-first or LD_PRELOAD GroundingDINO attempts for
paper claims. The non-dino-first attempt encountered late-import model-provider
unavailability, and the LD_PRELOAD attempt triggered SAPIEN/CUDA runner
exceptions in a full run.

## Open-Vocab Bridge v2 and Closed-Loop Sanity

The next IEEE Access revision experiments are intentionally smaller than the
main diagnostic corpus and target the strongest residual reviewer risks:

```bash
DATE_TAG=20260520 bash scripts/run_h200_open_vocab_bridge_v2_queue.sh
DATE_TAG=20260520 bash scripts/run_h200_closed_loop_sanity_queue.sh
```

The Open-Vocab Bridge v2 queue uses GPU1--3, runs the 144-episode smoke first,
and only then launches the 13,500-episode full bridge. The closed-loop sanity
queue uses the scripted ManiSkill executor runner and requires at least 80%
oracle smoke task success before the 4,800-episode subset is considered valid.

Supplementary analyses for completed JSON roots can be regenerated with:

```bash
python scripts/generate_ieee_access_supplement_analysis.py \
  --roots Heldout=/data/openMythosBench_project/outputs/weekend_main_v1_seed350_650_20260516 \
          BridgeV2=/data/openMythosBench_project/outputs/open_vocab_bridge_v2_20260520 \
  --output-dir ieee_access_revision_20260520/supplement_analysis \
  --figures-dir paper/ieee_access/figures/supplement
```

## Duplicate Result Check

```bash
ROOT=<OUTPUT_ROOT>
find "$ROOT" -name "*.json" ! -name "experiment_config_snapshot.json" -printf "%f\n" | sort | uniq -d | wc -l
```

Expected value: `0`.

## Resume Interrupted Runs

The sharded runner skips existing JSON outputs. Relaunch the same config and
same output root with the same shard count or a compatible resume script.

## JSON Schema

See:

- `schemas/episode_result_schema.json`
- `docs/json_schema_example.md`

## Required Artifacts for Paper Numbers

To reproduce all IEEE Access revision numbers, a reviewer needs:

- source code at the submitted commit
- YAML configs
- full JSON output roots or regenerated runs
- generated CSV tables under `ieee_access_revision_20260520/`
- generated LaTeX tables under `paper/ieee_access/tables/`
- generated figures under `paper/ieee_access/figures/`
