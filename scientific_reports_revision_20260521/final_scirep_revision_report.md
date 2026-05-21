# Scientific Reports Revision Report

Date: 2026-05-21

## What Changed

- Generated Scientific Reports result-to-claim assets from completed JSON/CSV artifacts.
- Added a standalone Scientific Reports manuscript draft under `paper/scientific_reports/`.
- Integrated the completed Open-Vocab Bridge v2 and YCB/clutter held-out bridge as detector-transfer evidence.
- Added a closed-loop oracle calibration v2 gate that explicitly downgrades execution calibration to an unresolved limitation.
- Updated claim-evidence documentation to prevent unsupported closed-loop, real-robot, or VLA-policy claims.
- Expanded Scientific Reports related work coverage to 36 cited references.
- Rewrote Data and Code Availability around the public GitHub repository and a staged release package.
- Added a GroundingDINO query-ablation config and a YCB target-name probe to test whether true object-name prompting is claimable.

## Generated Evidence

- Open-Vocab Bridge v2: 13,500/13,500 episodes, duplicate count 0, runner exceptions 0.
- YCB/clutter held-out bridge: 18,000/18,000 episodes, duplicate count 0, runner exceptions 0.
- Closed-loop smoke: 80/80 episodes, duplicate count 0, runner exceptions 0, oracle task success 0.0.
- Closed-loop oracle calibration v2: 20/20 smoke episodes, duplicate count 0, oracle task success 0.10; gate failed, so full calibration was skipped.
- ManiSkill qualitative render export: 5 artifact-backed RGB/depth cases exported on H200.
- GroundingDINO query ablation: 3,840/3,840 episodes, duplicate count 0, runner exceptions 0.
- YCB target-name probe: 20/20 rows, 0 non-generic target-label rows; true object-name prompt ablation is not claimable from the current adapter.

## Paper Routing

Supported:

- Parameterized simulation stressors expose target-generation failures.
- RGB-D target sources show a precision--robustness tradeoff.
- Open-vocabulary detector plug-ins can be evaluated through the same protocol.
- Detector and adapter-label limitations are measurable through no-detection and wrong-detection outcomes.

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
- `paper/scientific_reports/figures/open_vocab_detector_transfer_success.png`
- `paper/scientific_reports/figures/open_vocab_detector_transfer_no_detection.png`
- `paper/scientific_reports/figures/maniskill_qualitative/maniskill_qualitative/maniskill_qualitative_figure.png`
- `scientific_reports_revision_20260521/qualitative_case_manifest.csv`
- `scientific_reports_revision_20260521/release_package/`
- `configs/experiments/open_vocab_query_ablation_ycb_clutter.yaml`
- `configs/experiments/closed_loop_oracle_calibration_v2_smoke.yaml`
- `configs/experiments/closed_loop_oracle_calibration_v2.yaml`
- `configs/experiments/open_vocab_true_name_query_ablation_ycb_clutter.yaml`
- `paper/scientific_reports/tables/query_ablation_summary.tex`
- `scientific_reports_revision_20260521/query_ablation_audit.md`
- `docs/scientific_reports_result_to_claim.md`
- `docs/claim_evidence_table_scientific_reports.md`

## Verification

- `python scripts/generate_scirep_revision_assets.py`: passed.
- `python scripts/build_scirep_release_package.py`: passed.
- `python -m pytest -q tests`: passed, 25 tests.
- Query-ablation audit: 3,840/3,840 episodes, duplicate count 0, runner exceptions 0.
- Closed-loop oracle calibration v2 gate: failed at PickCube 0.10 and PickSingleYCB 0.10 oracle task success.
- Target-name probe: confirmed generic YCB target labels, so true-name ablation was stopped and partial files are ignored.
- Scientific Reports manuscript citation coverage: 36 unique cited references.
- Manuscript availability scan: no `[repository/DOI]`, `must not be treated`, or placeholder wording remains in the paper text.
- LaTeX source audit: all `\input{}` files and citation keys resolve.
- `git diff --check`: no whitespace errors; line-ending warnings only.
- GitHub main branch and annotated release tag `v0.1.0-scirep` were pushed.
- The release tag resolves to the exact archived commit for the submitted source package.
- PDF build was not completed locally because `pdflatex`, `latexmk`, and
  `tectonic` are not installed, and Docker Desktop is present but its daemon is
  not running.

## Next Steps

1. Compile and visually inspect the Scientific Reports PDF.
2. Create the GitHub release from tag `v0.1.0-scirep` and upload
   `scientific_reports_revision_20260521/release_package_v0.1.0-scirep.zip`.
3. Archive the GitHub release with Zenodo and replace the release-package DOI
   placeholder with the minted DOI.
4. Add the minted DOI to the Data and Code Availability sections before submission.
5. Revisit closed-loop calibration only after a scripted executor passes the oracle gate.
