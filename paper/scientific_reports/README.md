# Scientific Reports Manuscript Draft

Title:

> A reproducible diagnostic benchmark for language-to-target generation in robotic manipulation

Author and correspondence:

> Zhuo Chen, zhuoc@chalmers.se

Canonical entry point:

```bash
cd paper/scientific_reports
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

This draft is scoped as a reproducible simulation study of language-to-target
generation failures. It must not be used to claim real-robot robustness,
closed-loop policy performance, or calibrated execution success until a
validated closed-loop executor passes the oracle gate.

Key generated assets:

- `tables/open_vocab_detector_transfer_summary.tex`
- `tables/query_ablation_summary.tex`
- `tables/closed_loop_oracle_calibration_v2_gate.tex`
- `figures/open_vocab_detector_transfer_combined.png`
- `figures/maniskill_qualitative_main_figure.png`
- `docs/scientific_reports_result_to_claim.md`

Before submission, freeze the public GitHub release and insert the Zenodo DOI
for the source-data package in the Data Availability section.
