# EmbodiedStressBench

EmbodiedStressBench is a reproducible diagnostic benchmark for query-conditioned
3D target localization in robotic manipulation. The project studies where a
language or object query becomes an executable 3D target, separating detector or
selector behavior, RGB-D target lifting, stressor sensitivity, and downstream
execution-calibration boundaries.

Current manuscript target:

> Scientific Reports

Canonical manuscript title:

> EmbodiedStressBench: A Reproducible Simulation Diagnostic for
> Query-Conditioned 3D Target Localization in Robotic Manipulation

Public repository:

> https://github.com/KleinChen42/EmbodiedStressBench.git

Author and correspondence:

> Zhuo Chen, zhuoc@chalmers.se

The source-data release is intended to be frozen as GitHub release
`v0.1.0-scirep` and archived with Zenodo before journal submission. The Zenodo
DOI is intentionally not hard-coded until the author mints the archive.

## What The Paper Claims

Supported claims:

- Parameterized simulation stressors expose target-generation failure modes.
- Target sources show a precision--robustness tradeoff: box-center targets are
  more precise under strict thresholds, while crop-median targets are stronger
  at the default and relaxed thresholds.
- Open-vocabulary detector modules can be audited through the same protocol,
  with GroundingDINO used as a scoped plug-in detector rather than as a detector
  leaderboard.
- External YCB-V/BOP RGB-D validation separates RGB-D lifting controls from
  detector/query failure without claiming real-robot manipulation.
- The scripted closed-loop oracle-gate audit fails; execution calibration is
  therefore reported as a limitation and claim boundary.

Not claimed:

- No real-robot robustness.
- No closed-loop policy benchmark.
- No SOTA VLA comparison.
- No claim that GroundingDINO generally fails beyond the tested query/adaptor
  setting.
- No claim that crop-median depth is universally best.

## Manuscript Source

Compile the Scientific Reports draft from:

```text
paper/scientific_reports/main.tex
```

The manuscript includes:

- main source and sections under `paper/scientific_reports/`;
- generated tables under `paper/scientific_reports/tables/`;
- generated figures under `paper/scientific_reports/figures/`;
- bibliography under `paper/scientific_reports/references.bib`;
- supplementary table entry point
  `paper/scientific_reports/supplementary_tables.tex`.

If a LaTeX toolchain is available:

```bash
cd paper/scientific_reports
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

## Repository Layout

- `embodied_stressbench/`: benchmark code and target-source implementations.
- `configs/experiments/`: reproducible experiment matrices.
- `configs/stressors/`: parameterized stressor definitions.
- `scripts/`: analysis, plotting, remote launch, and release helpers.
- `paper/scientific_reports/`: current Scientific Reports manuscript source.
- `scientific_reports_revision_20260521/`: generated source data, revision
  reports, release-package staging, and reviewer prompts.
- `schemas/`: episode-result schema documentation.
- `tests/`: unit and regression tests.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
python -m pytest -q tests
```

Run a small mock matrix:

```bash
python -m embodied_stressbench.runners.run_matrix \
  --config configs/experiments/exp_tiny_mock.yaml \
  --output outputs/tiny_mock
```

Generate a report:

```bash
python -m embodied_stressbench.reporting.make_report \
  --input outputs/tiny_mock \
  --output outputs/tiny_mock/report.md
```

## Reproducing Paper Assets

See [README_REPRODUCIBILITY.md](README_REPRODUCIBILITY.md) for the
Scientific Reports source-data package, expected evidence sets, and commands to
regenerate tables and figures.

The staged release package is:

```text
scientific_reports_revision_20260521/release_package/
```

The current GitHub/Zenodo preparation checklist is:

```text
docs/scirep_data_code_release_checklist.md
```

## Secrets And Remote Helpers

Some helper scripts support remote experiment launch and artifact sync. Local
secrets must live in `.env.local`, which must not be committed. Use
`.env.local.example` only as a template.

## Safety And Scope

EmbodiedStressBench is a diagnostic study of query-to-3D-target generation. It
does not claim calibrated closed-loop manipulation performance or real-robot
deployment robustness.
