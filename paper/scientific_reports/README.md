# Scientific Reports Manuscript Draft

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
- `tables/closed_loop_smoke_outcome.tex`
- `figures/open_vocab_detector_transfer_success.png`
- `figures/open_vocab_detector_transfer_no_detection.png`
- `docs/scientific_reports_result_to_claim.md`

Before submission, replace `[repository/DOI]` placeholders with a real code and
artifact release.
