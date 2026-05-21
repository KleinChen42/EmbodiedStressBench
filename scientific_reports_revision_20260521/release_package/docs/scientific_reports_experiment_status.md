# Scientific Reports Experiment Status

Date: 2026-05-21

## Overnight Outcome

The GPU1--3 overnight queue completed the planned evidence-gated route. The
closed-loop smoke failed the oracle execution gate, so the queue correctly
switched to the YCB/clutter Open-Vocab Bridge held-out fallback.

| Evidence set | Status | Episodes | Duplicate results | Runner exceptions | Paper use |
| --- | --- | ---: | ---: | ---: | --- |
| Open-Vocab Bridge v2 | complete | 13,500/13,500 | 0 | 0 | learned-detector bridge |
| Closed-loop sanity smoke | complete | 80/80 | 0 | 0 | audit only; gate failed |
| YCB/clutter bridge held-out | complete | 18,000/18,000 | 0 | 0 | detector-query and adapter-label limitation |

## Key Claim Decision

The Scientific Reports manuscript can support detector-agnostic target-generation
diagnosis and open-vocabulary detector plug-in evaluation. It cannot yet support
a positive claim that diagnostic target success predicts scripted execution
success, because oracle task success was 0.0 in the closed-loop smoke.

## Generated Local Artifacts

- `docs/scientific_reports_result_to_claim.md`
- `docs/claim_evidence_table_scientific_reports.md`
- `scientific_reports_revision_20260521/scirep_open_vocab_detector_transfer_combined.csv`
- `paper/scientific_reports/tables/open_vocab_detector_transfer_summary.tex`
- `paper/scientific_reports/tables/closed_loop_smoke_outcome.tex`
- `paper/scientific_reports/figures/open_vocab_detector_transfer_success.png`
- `paper/scientific_reports/figures/open_vocab_detector_transfer_no_detection.png`
- `paper/scientific_reports/figures/maniskill_qualitative/maniskill_qualitative/maniskill_qualitative_figure.png`
- `scientific_reports_revision_20260521/qualitative_case_manifest.csv`
- `paper/scientific_reports/main.tex`
- `scientific_reports_revision_20260521/release_package/`
- `configs/experiments/open_vocab_query_ablation_ycb_clutter.yaml`

## Completed Query-Ablation Follow-up

The GroundingDINO YCB/clutter query-ablation queue completed on H200 GPU1--3.

- Output root: `/data/openMythosBench_project/outputs/open_vocab_query_ablation_ycb_clutter_20260521`
- Log: `/data/openMythosBench_project/outputs/open_vocab_query_ablation_ycb_clutter_20260521.log`
- Analysis root: `/data/openMythosBench_project/outputs/scirep_query_ablation_20260521`
- Query variants: generic, object-label template, category template, label phrase.
- Completed episodes: 3,840/3,840.
- Duplicate result count: 0.
- Runner exceptions: 0.
- GroundingDINO debug fields: 1,920/1,920 rows.
- Paper interpretation: prompt variants remove the previous no-detection mode but remain dominated by wrong-detection failures; current YCB labels are still generic, so this is detector-query sensitivity plus adapter-metadata limitation, not true object-name prompt recovery.

## Next Actions

1. Compile and visually inspect `paper/scientific_reports/main.tex`.
2. Create the GitHub release and Zenodo archive before submission.
3. Reattempt closed-loop calibration only after a scripted executor passes the
   oracle gate.
