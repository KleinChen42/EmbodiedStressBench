# IEEE Access Artifact Checklist

| Item | Status | Location / Notes |
| --- | --- | --- |
| Code available | Ready locally | `embodied_stressbench/`, `scripts/` |
| Experiment configs available | Ready | `configs/experiments/` |
| Stressor configs available | Ready | `configs/stressors/` |
| Stressor parameter table generated | Ready | `paper/ieee_access/tables/stressor_parameter_table.tex` |
| JSON result schema documented | Ready | `schemas/episode_result_schema.json` |
| JSON schema example documented | Ready | `docs/json_schema_example.md` |
| Main reports generated | Ready on H200 | `report.md` in each output root |
| Figures regenerated from scripts | Ready | `scripts/generate_ieee_access_ci_figures.py`, `scripts/generate_paper_diagrams.py` |
| Tables regenerated from scripts | Ready | `scripts/analyze_ieee_access_statistics.py`, `scripts/generate_stressor_table.py` |
| Main/supplement table split | Ready | Main compact tables in `paper/ieee_access/tables/`; long tables in `paper/ieee_access/tables/supplement/` |
| Canonical manuscript source guarded | Ready | Compile `paper/ieee_access/main_revised.tex`; `paper/main.tex` intentionally errors |
| Confidence intervals generated | Ready | `ieee_access_revision_20260520/*_with_ci.csv` |
| Threshold sensitivity generated | Ready | `ieee_access_revision_20260520/threshold_sensitivity.csv` |
| Seed splits documented | Ready | `README_REPRODUCIBILITY.md` |
| Duplicate-file check documented | Ready | `README_REPRODUCIBILITY.md` |
| Resume procedure documented | Ready | `README_REPRODUCIBILITY.md` |
| Open-vocabulary detector plug-in | Ready | `embodied_stressbench/detectors/clip_rerank.py`, `embodied_stressbench/detectors/grounding_dino.py` |
| Open-vocabulary results | GroundingDINO bridge ready | `ieee_access_revision_20260520/open_vocab_detector_bridge_dino_first9/`; CLIP remains unreported because the model cache/network was unavailable |
| Real-robot validation | Not run | Stated as limitation |
| Closed-loop policy rollout | Not run | Stated as limitation |
| PDF compiled | Blocked locally | See `ieee_access_revision_20260520/pdf_build_status.md`; `pdflatex`/`latexmk` unavailable and Docker daemon unreachable |
