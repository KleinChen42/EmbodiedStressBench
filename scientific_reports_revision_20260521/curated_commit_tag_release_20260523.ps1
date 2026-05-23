$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

$ReleaseTag = "v0.1.0-scirep"
$CommitMessage = "Finalize Scientific Reports release package"
$ReleaseDir = "scientific_reports_revision_20260521\release_package_doi_final_release"
$ReleaseZip = "scientific_reports_revision_20260521\release_package_v0.1.0-scirep_20260523_doi_final_release.zip"
$OverleafZip = "scientific_reports_revision_20260521\scientific_reports_overleaf_final_20260523_doi_release.zip"
$ChecksumCsv = "scientific_reports_revision_20260521\doi_final_release_zip_checksums_sha256.csv"

$Included = @(
  ".gitignore",
  "README.md",
  "README_REPRODUCIBILITY.md",
  "LICENSE",
  "CITATION.cff",
  "configs/experiments/main_v1_ieee_access.yaml",
  "configs/experiments/open_vocab_bridge_v2.yaml",
  "configs/experiments/open_vocab_query_ablation_ycb_clutter.yaml",
  "configs/experiments/closed_loop_oracle_gate_audit_200.yaml",
  "configs/experiments/open_vocab_true_name_ablation_small.yaml",
  "configs/experiments/scirep_oracle_2d_box_control.yaml",
  "configs/experiments/scirep_oracle_2d_box_control_smoke.yaml",
  "docs/SCIREP_CLAIM_EVIDENCE.md",
  "docs/claim_evidence_table_scientific_reports.md",
  "docs/scientific_reports_experiment_status.md",
  "docs/scientific_reports_result_to_claim.md",
  "docs/scirep_data_code_release_checklist.md",
  "paper/main.tex",
  "paper/scientific_reports",
  "scientific_reports_revision_20260521/chatgpt_pro_review_prompt_20260523.md",
  "scientific_reports_revision_20260521/final_scirep_revision_report.md",
  "scientific_reports_revision_20260521/qualitative_case_manifest.csv",
  "scientific_reports_revision_20260521/query_ablation_audit.md",
  "scientific_reports_revision_20260521/query_ablation_summary.csv",
  "scientific_reports_revision_20260521/scirep_open_vocab_detector_transfer_combined.csv",
  "scientific_reports_revision_20260521/target_name_probe_summary.csv",
  "scientific_reports_revision_20260521/external_rgbd_by_object.csv",
  "scientific_reports_revision_20260521/external_rgbd_by_scene.csv",
  "scientific_reports_revision_20260521/external_rgbd_detector_threshold_sensitivity_note.md",
  "scientific_reports_revision_20260521/external_rgbd_validation_claim_note.md",
  "scientific_reports_revision_20260521/low_iou_valid_3d_summary.csv",
  "scientific_reports_revision_20260521/main_diagnostic_summary.csv",
  "scientific_reports_revision_20260521/paired_effects_scirep.csv",
  "scientific_reports_revision_20260521/target_source_threshold_tradeoff_source.csv",
  "scripts/build_scirep_release_package.py",
  "scripts/generate_scirep_revision_assets.py",
  "scripts/generate_scirep_external_rgbd_assets.py",
  "scripts/generate_scirep_ycbv_threshold_sweep_assets.py",
  "scripts/analyze_ycbv_external_rgbd_probe.py",
  "scripts/run_ycbv_external_rgbd_probe.py"
)

Write-Host "== Curated staging =="
git rm -r --cached --ignore-unmatch -- scientific_reports_revision_20260521/release_package
git add -- $Included
git diff --cached --check
git diff --cached --name-status

Write-Host "== Commit =="
$HasStaged = git diff --cached --quiet; $ExitCode = $LASTEXITCODE
if ($ExitCode -eq 0) {
  Write-Host "No staged changes; skipping commit."
} else {
  git commit -m $CommitMessage
}
$Commit = git rev-parse HEAD
Write-Host "Release commit: $Commit"

Write-Host "== Rebuild release artifacts with exact commit metadata =="
python scripts/build_scirep_release_package.py --output $ReleaseDir
if (Test-Path $ReleaseZip) { Remove-Item -LiteralPath $ReleaseZip -Force }
if (Test-Path $OverleafZip) { Remove-Item -LiteralPath $OverleafZip -Force }
Compress-Archive -Path "$ReleaseDir\*" -DestinationPath $ReleaseZip -Force
Compress-Archive -Path "paper\scientific_reports\*" -DestinationPath $OverleafZip -Force
$Rows = foreach ($Item in @($ReleaseZip, $OverleafZip)) {
  $Hash = Get-FileHash -Algorithm SHA256 $Item
  [pscustomobject]@{ sha256 = $Hash.Hash.ToLower(); path = $Item }
}
$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 $ChecksumCsv
$Rows | Format-Table -AutoSize

Write-Host "== Tag and push =="
git tag -fa $ReleaseTag -m "Scientific Reports release package ($Commit)"
git push origin main
git push origin $ReleaseTag --force

Write-Host "== GitHub Release =="
$Gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $Gh) {
  Write-Warning "GitHub CLI 'gh' is not installed. Main and tag were pushed, but release assets were not uploaded automatically."
  Write-Host "Create/update release $ReleaseTag at https://github.com/KleinChen42/EmbodiedStressBench/releases and upload:"
  Write-Host "  $ReleaseZip"
  Write-Host "  $OverleafZip"
  Write-Host "  $ChecksumCsv"
  exit 0
}

$ReleaseNotes = @"
Scientific Reports release package for:

A reproducible diagnostic benchmark for language-to-target generation in robotic manipulation

- Zenodo version DOI: https://doi.org/10.5281/zenodo.20351628
- Zenodo concept DOI: https://doi.org/10.5281/zenodo.20351620
- Release commit: $Commit
- License: MIT

Assets:
- DOI-final source-data/code release package
- DOI-final Overleaf manuscript source zip
- SHA256 checksum CSV
"@
$NotesPath = "scientific_reports_revision_20260521\github_release_notes_20260523.md"
$ReleaseNotes | Set-Content -Encoding UTF8 $NotesPath

gh release view $ReleaseTag *> $null
if ($LASTEXITCODE -eq 0) {
  gh release edit $ReleaseTag --title "Scientific Reports release package" --notes-file $NotesPath --target $Commit
} else {
  gh release create $ReleaseTag --title "Scientific Reports release package" --notes-file $NotesPath --target $Commit
}
gh release upload $ReleaseTag $ReleaseZip $OverleafZip $ChecksumCsv --clobber

Write-Host "Done."
