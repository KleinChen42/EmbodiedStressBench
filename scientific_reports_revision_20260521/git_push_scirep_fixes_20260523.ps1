$ErrorActionPreference = "Stop"

# Run from the repository root:
#   powershell -ExecutionPolicy Bypass -File scientific_reports_revision_20260521\git_push_scirep_fixes_20260523.ps1
#
# This stages the Scientific Reports manuscript, source-data tables, figure assets,
# release-package metadata, and the code/config changes needed to regenerate the
# reported claims. It intentionally does not add local paper*.zip exports or the
# old IEEE Access scratch directory.

$files = @(
  ".env.local.example",
  "README.md",
  "README_REPRODUCIBILITY.md",

  "configs/experiments/closed_loop_oracle_gate_audit_200.yaml",
  "configs/experiments/open_vocab_true_name_ablation_debug_gdino.yaml",
  "configs/experiments/open_vocab_true_name_ablation_small.yaml",
  "configs/experiments/scirep_oracle_2d_box_control.yaml",
  "configs/experiments/scirep_oracle_2d_box_control_smoke.yaml",

  "docs/claim_evidence_table_scientific_reports.md",
  "docs/scientific_reports_experiment_status.md",
  "docs/scientific_reports_result_to_claim.md",
  "docs/scirep_data_code_release_checklist.md",

  "embodied_stressbench/baselines/registry.py",
  "embodied_stressbench/baselines/rgbd_crop.py",
  "embodied_stressbench/envs/maniskill_env.py",
  "embodied_stressbench/runners/run_matrix.py",

  "paper/scientific_reports/README.md",
  "paper/scientific_reports/main.tex",
  "paper/scientific_reports/supplementary_tables.tex",
  "paper/scientific_reports/sections",
  "paper/scientific_reports/tables",
  "paper/scientific_reports/figures/protocol_schematic.pdf",
  "paper/scientific_reports/figures/protocol_schematic.png",
  "paper/scientific_reports/figures/open_vocab_detector_transfer_combined.pdf",
  "paper/scientific_reports/figures/open_vocab_detector_transfer_combined.png",
  "paper/scientific_reports/figures/open_vocab_detector_transfer_combined_source.csv",
  "paper/scientific_reports/figures/external_rgbd_validation.pdf",
  "paper/scientific_reports/figures/external_rgbd_validation.png",
  "paper/scientific_reports/figures/external_rgbd_validation.svg",
  "paper/scientific_reports/figures/external_rgbd_validation_source.csv",
  "paper/scientific_reports/figures/external_rgbd_detector_threshold_sensitivity.pdf",
  "paper/scientific_reports/figures/external_rgbd_detector_threshold_sensitivity.png",
  "paper/scientific_reports/figures/external_rgbd_detector_threshold_sensitivity.svg",
  "paper/scientific_reports/figures/external_rgbd_detector_threshold_sensitivity_source.csv",
  "paper/scientific_reports/figures/target_source_threshold_tradeoff.pdf",
  "paper/scientific_reports/figures/target_source_threshold_tradeoff.png",
  "paper/scientific_reports/figures/target_source_threshold_tradeoff_source.csv",
  "paper/scientific_reports/figures/qualitative_failure_teaser.pdf",
  "paper/scientific_reports/figures/qualitative_failure_teaser.png",
  "paper/scientific_reports/figures/maniskill_qualitative_main_figure.pdf",
  "paper/scientific_reports/figures/maniskill_qualitative_main_figure.png",
  "paper/scientific_reports/figures/maniskill_qualitative",

  "scripts/analyze_closed_loop_sanity.py",
  "scripts/analyze_ycbv_external_rgbd_probe.py",
  "scripts/build_scirep_release_package.py",
  "scripts/check_grounding_dino_runtime.py",
  "scripts/download_ycbv_bop_external_data.py",
  "scripts/download_ycbv_bop_hfmirror_aria2.sh",
  "scripts/generate_scirep_external_rgbd_assets.py",
  "scripts/generate_scirep_revision_assets.py",
  "scripts/generate_scirep_ycbv_threshold_sweep_assets.py",
  "scripts/probe_maniskill_target_identity_deep.py",
  "scripts/probe_maniskill_target_names.py",
  "scripts/run_h200_scirep_oracle_2d_box_control.sh",
  "scripts/run_h200_scirep_p0_p1_followup.sh",
  "scripts/run_h200_true_name_ablation_only.sh",
  "scripts/run_h200_ycbv_external_rgbd_probe.sh",
  "scripts/run_h200_ycbv_external_rgbd_probe_160k.sh",
  "scripts/run_h200_ycbv_external_rgbd_threshold_sweep_after_160k.sh",
  "scripts/run_ycbv_external_rgbd_probe.py",
  "tests/test_task_queries.py",

  "scientific_reports_revision_20260521/chatgpt_pro_review_prompt_20260523.md",
  "scientific_reports_revision_20260521/final_scirep_revision_report.md",
  "scientific_reports_revision_20260521/git_push_scirep_fixes_20260523.ps1",
  "scientific_reports_revision_20260521/pdf_page_audit_20260523.md",
  "scientific_reports_revision_20260521/external_rgbd_validation_claim_note.md",
  "scientific_reports_revision_20260521/external_rgbd_detector_threshold_sensitivity_note.md",
  "scientific_reports_revision_20260521/query_ablation_audit.md",
  "scientific_reports_revision_20260521/qualitative_case_manifest.csv",
  "scientific_reports_revision_20260521/scirep_open_vocab_detector_transfer_combined.csv",
  "scientific_reports_revision_20260521/main_diagnostic_summary.csv",
  "scientific_reports_revision_20260521/low_iou_valid_3d_summary.csv",
  "scientific_reports_revision_20260521/paired_effects_scirep.csv",
  "scientific_reports_revision_20260521/external_rgbd_by_object.csv",
  "scientific_reports_revision_20260521/external_rgbd_by_scene.csv",
  "scientific_reports_revision_20260521/target_source_threshold_tradeoff_source.csv",
  "scientific_reports_revision_20260521/query_ablation_summary.csv",
  "scientific_reports_revision_20260521/target_name_probe_summary.csv",

  "scientific_reports_revision_20260521/release_package/README.md",
  "scientific_reports_revision_20260521/release_package/README_REPRODUCIBILITY.md",
  "scientific_reports_revision_20260521/release_package/CODE_DATA_RELEASE_METADATA.md",
  "scientific_reports_revision_20260521/release_package/release_manifest.csv",
  "scientific_reports_revision_20260521/release_package/configs",
  "scientific_reports_revision_20260521/release_package/docs",
  "scientific_reports_revision_20260521/release_package/figures",
  "scientific_reports_revision_20260521/release_package/paper",
  "scientific_reports_revision_20260521/release_package/paper_tables",
  "scientific_reports_revision_20260521/release_package/schemas",
  "scientific_reports_revision_20260521/release_package/scripts",
  "scientific_reports_revision_20260521/release_package/source_data/qualitative_case_manifest.csv",
  "scientific_reports_revision_20260521/release_package/source_data/scirep_open_vocab_detector_transfer_combined.csv",
  "scientific_reports_revision_20260521/release_package/source_data/tables",
  "scientific_reports_revision_20260521/release_package/source_data/p0_p1_followup_report.md"
)

git add -- $files
git diff --cached --check
git commit -m "Finalize Scientific Reports release revision"
git push origin main
