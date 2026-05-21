# Repository Inventory for IEEE Access Revision

Date: 2026-05-20

## Manuscript Sources

- Original paper entry: `paper/main.tex` (legacy guard; do not compile for submission)
- Original sections: `paper/sections/*.tex`
- IEEE Access revised entry: `paper/ieee_access/main_revised.tex`
- IEEE Access revised sections: `paper/ieee_access/sections/*.tex`
- Bibliography: `paper/references.bib`

## Experiment Configs

Completed or report-backed configs:

- `configs/experiments/exp_maniskill_smoke.yaml`
- `configs/experiments/exp_maniskill_pilot.yaml`
- `configs/experiments/main_v1_ieee_access.yaml`
- `configs/experiments/main_v1_ieee_access_confirmatory.yaml`
- `configs/experiments/main_v1_ieee_access_hard_l3_extension.yaml`
- `configs/experiments/weekend_main_v1_seed350_650.yaml`
- `configs/experiments/weekend_visual_sensor_bridge_seed350_500.yaml`
- `configs/experiments/weekend_hard_l3_seed650_800.yaml`
- `configs/experiments/semantic_distractor_validity_v1.yaml`

Implemented but not completed for paper claims:

- `configs/experiments/open_vocab_smoke.yaml`
- `configs/experiments/open_vocab_ieee_access_small.yaml`

Completed open-vocabulary bridge configs:

- `configs/experiments/open_vocab_grounding_dino_smoke.yaml`
- `configs/experiments/open_vocab_grounding_dino_ieee_access_small_dino_first.yaml`

## Result Directories

Remote H200 result roots used for generated paper artifacts:

- Main v1: `/data/openMythosBench_project/outputs/main_v1_ieee_access_20260514_full`
- Confirmatory: `/data/openMythosBench_project/outputs/main_v1_ieee_access_confirmatory_20260514`
- Hard L3 extension: `/data/openMythosBench_project/outputs/main_v1_ieee_access_hard_l3_extension_20260514`
- Held-out extension: `/data/openMythosBench_project/outputs/weekend_main_v1_seed350_650_20260516`
- Visual/sensor bridge: `/data/openMythosBench_project/outputs/weekend_visual_sensor_bridge_seed350_500_20260516`
- Hard L3 confirmation: `/data/openMythosBench_project/outputs/weekend_hard_l3_seed650_800_20260516`
- Semantic distractor validity: `/data/openMythosBench_project/outputs/semantic_distractor_validity_v1_20260518`
- GroundingDINO bridge smoke: `/data/openMythosBench_project/outputs/open_vocab_grounding_dino_smoke_20260520`
- GroundingDINO bridge small, final valid run: `/data/openMythosBench_project/outputs/open_vocab_grounding_dino_ieee_access_small_20260520_dino_first9`

Local generated artifacts:

- `paper/generated/*`: first-pass generated figures/tables
- `paper/ieee_access/tables/*`: IEEE Access revision tables
- `paper/ieee_access/tables/supplement/*`: long supplementary IEEE Access tables
- `paper/ieee_access/figures/*`: IEEE Access revision figures
- `ieee_access_revision_20260520/*.csv`: revision analysis CSVs

## JSON/CSV Schema

Episode JSON fields are produced by `embodied_stressbench/runners/run_single.py`.
Core fields:

- `task`
- `backend`
- `seed`
- `baseline`
- `query_original`
- `query_used`
- `stressor`
- `level`
- `stress_info`
- `success`
- `failure_type`
- `prediction`
- `execution_debug`
- `target_error_l2`
- `num_detections`
- `runtime_sec`

Report CSVs:

- `success_by_group.csv`
- `oracle_gap_by_group.csv`

Revision CSVs:

- `main_results_with_ci.csv`
- `oracle_gap_with_ci.csv`
- `oracle_gap_by_stressor_with_ci.csv`
- `stressor_ranking_with_ci.csv`
- `failure_distribution_with_ci.csv`
- `threshold_sensitivity.csv`
- `stressor_parameter_table.csv`

## Existing Baselines and Selectors

Target sources:

- `oracle_target`
- `box_center_depth`
- `crop_median_depth`
- `crop_top_surface`
- query-aware and first-detection variants for semantic validity

Selector code:

- `embodied_stressbench/perception/detection_selection.py`

Target-source code:

- `embodied_stressbench/baselines/rgbd_crop.py`
- `embodied_stressbench/baselines/oracle_target.py`

Detector extension interface:

- `embodied_stressbench/detectors/base.py`
- `embodied_stressbench/detectors/metadata_oracle.py`
- `embodied_stressbench/detectors/first_detection.py`
- `embodied_stressbench/detectors/clip_rerank.py`
- `embodied_stressbench/detectors/grounding_dino.py`

Open-vocabulary bridge configs:

- `configs/experiments/open_vocab_grounding_dino_smoke.yaml`
- `configs/experiments/open_vocab_grounding_dino_ieee_access_small.yaml`
- `configs/experiments/open_vocab_grounding_dino_ieee_access_small_dino_first.yaml`

## Stressor Implementations

Implementation:

- `embodied_stressbench/stressors/registry.py`

Parameterized YAML configs:

- `configs/stressors/*.yaml`

Generated table:

- `paper/ieee_access/tables/stressor_parameter_table.tex`
- `ieee_access_revision_20260520/stressor_parameter_table.csv`

## Paper Number Traceability

Hard-coded legacy numbers still exist in `paper/sections/results.tex` from
earlier drafting. The submission entry is `paper/ieee_access/main_revised.tex`;
`paper/main.tex` intentionally errors if compiled. The IEEE Access revision
should use generated compact tables under `paper/ieee_access/tables/`,
supplementary long tables under `paper/ieee_access/tables/supplement/`, and
generated CSV files under `ieee_access_revision_20260520/`.

Numbers that can be regenerated:

- Baseline success with CI: `scripts/analyze_ieee_access_statistics.py`
- Oracle gap with CI: `scripts/analyze_ieee_access_statistics.py`
- Stressor ranking with CI: `scripts/analyze_ieee_access_statistics.py`
- Failure distribution with CI: `scripts/analyze_ieee_access_statistics.py`
- Threshold sensitivity: `scripts/analyze_threshold_sensitivity.py`
- Stressor parameters: `scripts/generate_stressor_table.py`
- Optional open-vocabulary detector bridge: `scripts/analyze_open_vocab_detector_bridge.py`
- Publication-readable main/supplement table rendering:
  `scripts/render_ieee_access_tables_from_csv.py`
- Figures: `scripts/generate_ieee_access_ci_figures.py`,
  `scripts/generate_paper_figures.py`, and `scripts/generate_paper_diagrams.py`

Missing or incomplete:

- CLIP crop-rerank experiment is implemented but blocked on missing local model
  cache and no Hugging Face network access on the H200 node.
- GroundingDINO smoke completed on H200 with zero runner exceptions. The final
  dino-first 1,200-episode bridge run completed on GPU1--3 with zero
  no-detection failures, zero runner exceptions, and zero duplicate result
  filenames. Earlier non-dino-first and LD_PRELOAD attempts are retained only
  as audit records and should not be used for manuscript claims.
- Real-robot validation has not been run.
- Local PDF compilation is blocked because `pdflatex`/`latexmk` is unavailable
  and Docker Desktop is not reachable in the current Windows environment. The
  current build status is recorded in `ieee_access_revision_20260520/pdf_build_status.md`.
