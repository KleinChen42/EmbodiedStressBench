# Scientific Reports PDF Page Audit (2026-05-23)

Audited PDF:
`E:/WebDownload/A_reproducible_diagnostic_benchmark_for_language_to_target_generation_in_robotic_manipulation__1_.pdf`

Rendered audit artifacts:
`scientific_reports_revision_20260521/pdf_page_audit_20260523_current/page_01.png` through `page_11.png`

## Executive Findings

1. **P0 layout failure: page 3 Table 1 exceeds the right page boundary.**
   The rendered page-boundary scan detected right-edge overflow, and visual inspection showed the five-column experimental design table running past the page edge.

   Fixed in source by rewriting `paper/scientific_reports/tables/experiment_design_summary.tex` as a compact three-column wrapped table and by updating `scripts/generate_scirep_revision_assets.py` so regeneration cannot restore the old five-column layout.

2. **P0 layout failure: page 8 Data/Code Availability reaches the right page boundary.**
   The rendered page-boundary scan detected right-edge overflow from bare DOI/GitHub URLs and a long commit string in the availability prose.

   Fixed in source by replacing bare `\url{...}` strings with short `\href{...}{...}` link text in `paper/scientific_reports/sections/data_availability.tex` and `paper/scientific_reports/sections/code_availability.tex`. The exact commit is now referenced through release metadata rather than printed as a long inline token in the PDF.

3. **DOI updated to the current Zenodo version DOI.**
   Active manuscript, release metadata, README, reproducibility README, `CITATION.cff`, and release-package builder now use version DOI `10.5281/zenodo.20352155`. The README badge target can remain the Zenodo concept/latest DOI `10.5281/zenodo.20351620`.

## Page-by-Page Audit

### Page 1

Status: acceptable.

No title, abstract, or first-page boundary failure was visible in the rendered page. The title is the current Scientific Reports diagnostic title.

### Page 2

Status: acceptable.

Figure 1 and related-work text remain inside the page boundary. No visible table overflow.

### Page 3

Status: **P0 layout failure in uploaded PDF, fixed in source.**

The uploaded PDF shows Table 1 extending beyond the right edge. Root cause was the normal five-column `tabular` layout:
`Evidence set`, `Tasks`, `Compared modules`, `Perturbations`, and `Statistical unit`.

Fix:
- changed Table 1 from `table*` to `table`;
- changed five unwrapped columns to three fixed-width paragraph columns;
- moved full task/stressor detail to Supplementary Table S1;
- updated the generator so future asset regeneration keeps the compact table.

### Page 4

Status: acceptable.

Figure 2 and Table 3 are inside the page boundary. No visible clipping in the rendered page.

### Page 5

Status: acceptable.

Figure 3 and Methods text are within the page boundary. The empty/no-detection panel is a presentation choice, not a page-overflow failure.

### Page 6

Status: acceptable.

Figure 4 is readable and inside the page boundary. No table overflow.

### Page 7

Status: acceptable with readability caveat.

Figure 5 fits the page. Panel text is small but not clipped in the rendered PDF.

### Page 8

Status: **P0 line-boundary failure in uploaded PDF, fixed in source.**

The uploaded PDF shows long DOI/repository text and a long commit token reaching the right boundary in Data Availability and Code Availability.

Fix:
- replaced bare DOI/GitHub URLs with short linked labels;
- removed the long inline commit hash from the manuscript prose;
- kept exact commit and checksum details in release metadata and the release package.

### Pages 9--11

Status: acceptable.

Reference pages are inside the page boundary in the rendered PDF. No overflow was detected on these pages.

## Rebuilt Artifacts

- Overleaf source zip: `scientific_reports_revision_20260521/scientific_reports_overleaf_final_20260523_doi_20352155_v1.zip`
- Release package directory: `scientific_reports_revision_20260521/release_package_doi_final_v7`
- Release package zip: `scientific_reports_revision_20260521/release_package_v0.1.0-scirep_doi_20352155.zip`

Local LaTeX is not installed in this Windows environment, so the final PDF must still be recompiled in Overleaf. The supplied Overleaf zip contains the fixed table source and updated availability sections.
