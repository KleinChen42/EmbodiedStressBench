# Scientific Reports Revision Report

Date: 2026-05-23

## What Changed

- Generated Scientific Reports result-to-claim assets from completed JSON/CSV artifacts.
- Added a standalone Scientific Reports manuscript draft under `paper/scientific_reports/`.
- Integrated the detector-bridge sweep as the main learned-detector evidence and downgraded the older YCB/clutter held-out bridge to auxiliary status because its GroundingDINO debug fields are absent.
- Added a 200-episode closed-loop oracle-gate audit that explicitly downgrades execution calibration to an unresolved limitation.
- Updated claim-evidence documentation to prevent unsupported closed-loop, real-robot, or VLA-policy claims.
- Expanded Scientific Reports related work coverage to 37 cited references.
- Rewrote Data and Code Availability around the public GitHub repository and a staged release package.
- Finalized release metadata with Zenodo version DOI `10.5281/zenodo.20352155`, release tag `v0.1.0-scirep`, MIT license, citation metadata, and checksum generation.
- Added a trusted YCB target-name probe and a 960-episode GroundingDINO true-name query ablation. The final ablation uses an explicit GroundingDINO warmup and `LD_PRELOAD` fix so detector debug fields are present.
- Integrated the full YCB-V/BOP external RGB-D validation run and the chained GroundingDINO detector-threshold sweep from archived experiment outputs, replacing the earlier 96k-record preliminary table.
- Reframed the Scientific Reports abstract, introduction, methods, discussion, and availability statements so the external YCB-V/BOP probe is presented as a main scope-check evidence pillar rather than an appendix-style add-on.

## Generated Evidence

- Detector-bridge sweep: 13,500/13,500 episodes, duplicate count 0, runner exceptions 0.
- YCB/clutter held-out bridge: 18,000/18,000 episodes, duplicate count 0, runner exceptions 0; auxiliary only because GroundingDINO debug fields are absent.
- Closed-loop smoke: 80/80 episodes, duplicate count 0, runner exceptions 0, oracle task success 0.0.
- Closed-loop oracle calibration v2: 20/20 smoke episodes, duplicate count 0, oracle task success 0.10; gate failed, so full calibration was skipped.
- Closed-loop 200-episode oracle-gate audit: 200/200 episodes, duplicate count 0, runner exceptions 0; PickCube and PickSingleYCB each achieved 2/100 oracle task success, so the execution gate remains failed.
- ManiSkill qualitative render export: 6 artifact-backed RGB/depth cases exported in the remote ManiSkill environment; the main figure uses four enlarged cases.
- GroundingDINO true-name query ablation: 960/960 episodes, duplicate count 0, runner exceptions 0; GroundingDINO debug fields are present for 468/480 learned-detector rows, no-detection rate is 0.013, and wrong-detection is the dominant learned-detector failure.
- YCB target-name probe: 40/40 rows resolved trusted target-specific names, enabling the true-name ablation.
- YCB-V/BOP external RGB-D validation: 1,577,072/1,577,072 records at the default detector threshold, failed shards 0. The full probe contains 98,567 object instances; oracle mask plus mask median reaches 99.97% success at 8 cm, oracle 2D boxes plus crop-trimmed median reach 79.9%, GroundingDINO generic prompts reach 23.8%, and true-name prompts reach 61.4%.
- YCB-V/BOP detector-threshold sweep: two additional full 1,577,072-record runs at GroundingDINO box/text thresholds 0.10/0.10 and 0.30/0.25, failed shards 0. True-name prompt success remains above generic prompt success across all three threshold settings.

## Paper Routing

Supported:

- Parameterized simulation stressors expose target-generation failures.
- RGB-D target sources show a precision--robustness tradeoff.
- One learned open-vocabulary detector plug-in can be evaluated through the same protocol alongside controlled selector comparators.
- Detector and adapter-label limitations are measurable through no-detection and wrong-detection outcomes.
- External real RGB-D source data can be used to separate RGB-D lifting controls from detector/query localization failures without making real-robot claims.

Not supported yet:

- Diagnostic target success predicts actual scripted task success.
- The benchmark validates a closed-loop policy.
- The results establish real-robot robustness.

## Main Files

- `paper/scientific_reports/main.tex`
- `paper/scientific_reports/sections/*.tex`
- `paper/scientific_reports/tables/open_vocab_detector_transfer_summary.tex`
- `paper/scientific_reports/tables/closed_loop_oracle_calibration_v2_gate.tex`
- `paper/scientific_reports/tables/target_name_probe_summary.tex`
- `paper/scientific_reports/figures/open_vocab_detector_transfer_combined.png`
- `paper/scientific_reports/figures/maniskill_qualitative_main_figure.png`
- `paper/scientific_reports/figures/maniskill_qualitative/maniskill_qualitative/maniskill_qualitative_figure.png`
- `scientific_reports_revision_20260521/qualitative_case_manifest.csv`
- `scientific_reports_revision_20260521/release_package/`
- `configs/experiments/closed_loop_oracle_gate_audit_200.yaml`
- `configs/experiments/open_vocab_true_name_ablation_small.yaml`
- `paper/scientific_reports/tables/query_ablation_summary.tex`
- `paper/scientific_reports/tables/external_rgbd_validation_summary.tex`
- `paper/scientific_reports/tables/external_rgbd_detector_threshold_sensitivity.tex`
- `paper/scientific_reports/figures/external_rgbd_validation.png`
- `paper/scientific_reports/figures/external_rgbd_detector_threshold_sensitivity.png`
- `scientific_reports_revision_20260521/query_ablation_audit.md`
- `scientific_reports_revision_20260521/external_rgbd_validation_claim_note.md`
- `scientific_reports_revision_20260521/external_rgbd_detector_threshold_sensitivity_note.md`
- `docs/scientific_reports_result_to_claim.md`
- `docs/claim_evidence_table_scientific_reports.md`

## Verification

- `python scripts/generate_scirep_revision_assets.py`: passed.
- `python scripts/build_scirep_release_package.py`: passed.
- `python -m pytest -q tests`: passed, 26 tests.
- Query-ablation audit: 960/960 episodes, duplicate count 0, runner exceptions 0.
- Closed-loop 200-episode audit: failed at PickCube 0.02 and PickSingleYCB 0.02 oracle task success; dominant failure is `no_grasp`.
- Target-name probe: recovered trusted YCB object names for 40/40 probed rows.
- Scientific Reports manuscript citation coverage: 37 BibTeX entries.
- Manuscript availability scan: no DOI placeholder, `must not be treated`, or other draft-only availability wording remains in the paper text.
- Remote YCB-V audit: default, 0.10/0.10, and 0.30/0.25 runs each completed 1,577,072 records with zero failed shards; each remote analysis directory contains a full `episode_index.csv` with 1,577,073 lines including the header.
- YCB-V local source-data package: reports, summary CSVs, threshold CSVs, generated tables, and generated figures were copied into the release package; the three large raw `episode_index.csv` files remain outside the lightweight release bundle and are recorded for separate archival if needed.
- LaTeX source audit: all `\input{}` files and citation keys resolve.
- `git diff --check`: no whitespace errors; line-ending warnings only.
- The P0/P1 release package was rebuilt under `scientific_reports_revision_20260521/release_package/`, including the full YCB-V/BOP summary source data and detector-threshold sweep logs.
- The manuscript text now explicitly describes the external YCB-V/BOP frame-block bootstrap confidence-interval unit and avoids the obsolete `simulation-only` limitation phrasing.
- A DOI-final release zip was created at `scientific_reports_revision_20260521/release_package_v0.1.0-scirep_20260523_doi_final.zip`; the matching Overleaf source zip is `scientific_reports_revision_20260521/scientific_reports_overleaf_final_20260523_doi.zip`.
- The manuscript and release metadata now cite Zenodo version DOI `10.5281/zenodo.20352155`.
- PDF build was not completed locally because `pdflatex`, `latexmk`, and
  `tectonic` are not installed, and Docker Desktop is present but its daemon is
  not running.

## Next Steps

1. Compile and visually inspect the Scientific Reports PDF.
2. Commit and push the final package cleanup, then make sure release tag
   `v0.1.0-scirep` points to the submitted package commit.
3. Create or refresh the GitHub release and upload the DOI-final release package.
4. Use Zenodo version DOI `10.5281/zenodo.20352155` in the submitted manuscript and repository metadata.
5. Revisit closed-loop calibration only after a scripted executor passes the oracle gate.
