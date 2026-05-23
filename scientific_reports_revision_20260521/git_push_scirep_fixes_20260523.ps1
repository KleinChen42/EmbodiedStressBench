$ErrorActionPreference = "Stop"

$files = @(
  "paper/scientific_reports/main.tex",
  "paper/scientific_reports/sections/data_availability.tex",
  "paper/scientific_reports/sections/code_availability.tex",
  "paper/scientific_reports/sections/results.tex",
  "paper/scientific_reports/tables/claim_support_matrix.tex",
  "paper/scientific_reports/tables/claim_support_matrix_full.tex",
  "paper/scientific_reports/supplementary_tables.tex",
  "paper/scientific_reports/figures/maniskill_qualitative_main_figure.png",
  "paper/scientific_reports/figures/maniskill_qualitative_main_figure.pdf",
  "scripts/generate_scirep_revision_assets.py",
  "scientific_reports_revision_20260521/chatgpt_pro_review_prompt_20260523.md",
  "scientific_reports_revision_20260521/git_push_scirep_fixes_20260523.ps1",
  "scientific_reports_revision_20260521/release_package/paper/scientific_reports/main.tex",
  "scientific_reports_revision_20260521/release_package/paper/scientific_reports/sections/data_availability.tex",
  "scientific_reports_revision_20260521/release_package/paper/scientific_reports/sections/code_availability.tex",
  "scientific_reports_revision_20260521/release_package/paper/scientific_reports/sections/results.tex",
  "scientific_reports_revision_20260521/release_package/paper_tables/claim_support_matrix.tex",
  "scientific_reports_revision_20260521/release_package/paper_tables/claim_support_matrix_full.tex",
  "scientific_reports_revision_20260521/release_package/figures/maniskill_qualitative_main_figure.png",
  "scientific_reports_revision_20260521/release_package/figures/maniskill_qualitative_main_figure.pdf",
  "scientific_reports_revision_20260521/release_package/scripts/generate_scirep_revision_assets.py"
)

git add -- $files
git diff --cached --check
git commit -m "Finalize Scientific Reports submission metadata"
git push origin main
