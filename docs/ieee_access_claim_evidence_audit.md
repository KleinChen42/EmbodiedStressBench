# IEEE Access Claim-Evidence Audit

Date: 2026-05-20

This audit follows the reviewer-facing rule that every major claim in the
abstract, introduction, and results must be supported by a generated artifact or
explicitly weakened.

| Claim | Evidence source | Status | Reviewer-facing wording control |
| --- | --- | --- | --- |
| EmbodiedStressBench is a diagnostic benchmark for the language-query-to-3D-target stage, not a closed-loop policy benchmark | `paper/ieee_access/sections/method_revised.tex`, `paper/ieee_access/sections/discussion_revised.tex` | Supported | Main text repeatedly says diagnostic target evaluation and avoids policy-superiority claims |
| The core evidence contains 434,240 ManiSkill diagnostic episodes | Episode counts listed in `paper/ieee_access/sections/experiments_revised.tex`; generated reports and CSVs under `ieee_access_revision_20260520/` | Supported | Abstract says "diagnostic episodes" rather than full robot trials |
| Target-source robustness gaps are stable across primary and held-out seeds | `ieee_access_revision_20260520/main_results_with_ci.csv`; `paper/ieee_access/tables/main_results_with_ci.tex` | Supported | Reported with seed-block bootstrap 95% CIs |
| Oracle gap separates task feasibility from target-generation failure | `ieee_access_revision_20260520/oracle_gap_with_ci.csv`; `paper/ieee_access/tables/oracle_gap_with_ci.tex` | Supported | Defined as success-rate difference, not causal proof beyond the diagnostic protocol |
| Semantic distractors create measurable wrong-detection failures | `ieee_access_revision_20260520/failure_distribution_with_ci.csv`; semantic selector figures and tables | Supported | Query-aware selector is described as metadata-based diagnostic comparator |
| Query-aware selection improves crop-median and box-center over first detection in the semantic run | `ieee_access_revision_20260520/main_results_with_ci.csv` | Supported | Results report percentage-point changes only for the semantic distractor validity run |
| Findings are threshold-sensitive but interpretable | `ieee_access_revision_20260520/threshold_sensitivity.csv`; `paper/ieee_access/tables/threshold_sensitivity.tex` | Supported | Text states ranking is not invariant at strict thresholds |
| Learned open-vocabulary detectors can be plugged into the benchmark | `ieee_access_revision_20260520/open_vocab_detector_bridge_dino_first9/*.csv`; `paper/ieee_access/tables/open_vocab_detector_bridge_dino_first9/*` | Supported as proof-of-concept | Text says small GroundingDINO bridge and avoids broad detector-performance claims |
| Open-vocabulary detector evidence beyond PickCube/YCB/clutter is being strengthened | `configs/experiments/open_vocab_bridge_v2*.yaml`; `scripts/run_h200_open_vocab_bridge_v2_queue.sh` | Running, not yet claimable | Do not add Bridge v2 numbers until JSON outputs and generated CSVs exist |
| Diagnostic target success has engineering relevance to actual task success | `configs/experiments/closed_loop_sanity*.yaml`; `embodied_stressbench/runners/run_closed_loop_sanity.py` | Interface implemented, not yet claimable | Report only after scripted executor smoke has >=80% oracle task success |
| Qualitative failure cases are traceable to artifacts | `ieee_access_revision_20260520/qualitative/qualitative_case_manifest.csv`; `paper/ieee_access/figures/qualitative_failure_teaser.pdf`; `scripts/generate_ieee_access_qualitative_figures.py` | Supported as visualization, not numerical evidence | Caption states the figure is generated from stored per-episode artifacts |
| EmbodiedStressBench is complementary to existing manipulation benchmarks | `paper/ieee_access/tables/benchmark_comparison_table.tex`; `ieee_access_revision_20260520/benchmark_comparison_table.csv`; related-work citations | Supported conceptually | Table compares evaluation focus and diagnostic affordances rather than claiming superiority |
| CLIP reranking is available as an interface | `embodied_stressbench/detectors/clip_rerank.py`; `configs/experiments/open_vocab_*.yaml` | Interface supported, result not claimed | Manuscript says CLIP is implemented but not reported numerically |
| The paper is reproducible from artifacts | `README_REPRODUCIBILITY.md`, `schemas/episode_result_schema.json`, `docs/artifact_checklist_ieee_access.md` | Mostly supported | Remaining limitation is public release or regeneration of full JSON outputs |
| The submission PDF must come from the revised IEEE Access source | `paper/ieee_access/main_revised.tex`; `paper/main.tex`; `scripts/build_ieee_access_pdf.ps1`; `ieee_access_revision_20260520/pdf_build_status.md` | Guarded | Legacy `paper/main.tex` intentionally errors and the build script records the canonical source |

## Remaining Reviewer Risks

- Full JSON artifacts still need a public release location or an explicit regeneration
  plan in the submission package.
- The GroundingDINO bridge is PickCube-only and should remain framed as plug-in
  feasibility until Open-Vocab Bridge v2 completes and is audited.
- The scripted closed-loop sanity subset is implemented but not yet completed,
  so no target-success/task-success correlation claim should be made.
- The qualitative teaser visualizes JSON debug metadata rather than raw RGB/depth
  frames because current completed artifacts do not store image files; the
  manifest makes each selected case auditable.
- Local PDF compilation is still blocked by missing LaTeX tooling and an
  unreachable Docker daemon, so final layout inspection remains pending.
