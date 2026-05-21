# Reviewer Self-Audit for IEEE Access Submission

Date: 2026-05-20

Target: IEEE Access first submission, with JINT-level rigor as the internal
quality bar.

## Editorial Triage

Likely decision if submitted after the current writing pass: major revision or
minor-to-major revision, depending on how strongly reviewers value real-robot
validation. The experimental evidence is now strong for a simulation diagnostic
benchmark, but presentation and positioning must stay disciplined.

## Reviewer 1: Methodology and Reproducibility

Strengths:

- Large completed evidence set: pilot, Main v1, confirmatory, held-out
  extension, visual/sensor bridge, hard level-3 confirmation, and semantic
  distractor validity.
- Reports are generated from JSON outputs, with duplicate-count checks and
  smoke gates.
- Oracle gap and failure taxonomy give more information than aggregate success.

Major risks:

- The paper must state the diagnostic success threshold and evaluation boundary
  clearly. This is now partially addressed by adding the 0.08 m threshold.
- Reviewers may ask whether all tables are generated from scripts. The answer
  should be supported by `scripts/generate_paper_tables.py`,
  `scripts/generate_paper_figures.py`, and `paper/generated/README.md`.
- Need final PDF compile check on a machine with LaTeX.

Required next fixes:

- Add a small reproducibility appendix or paragraph listing exact config files
  and output roots.
- Ensure every table caption says whether values are generated and from which
  run family.

## Reviewer 2: Robotics and Benchmark Fit

Strengths:

- Uses ManiSkill and YCB/clutter tasks, so the benchmark is grounded in known
  robotics simulation infrastructure.
- Separates target-generation diagnosis from policy rollout, which is useful
  for debugging language-conditioned pipelines.
- The simulation-only limitation is acknowledged directly.

Major risks:

- A robotics reviewer may object that there is no real robot or closed-loop
  policy. The paper must not overclaim deployment validity.
- Query-aware selection uses simulator metadata; it should be framed as a
  controlled diagnostic comparator, not a perception model.
- `execution_offset_strong` can reduce oracle success, so claims about
  target-source failure must separate execution-limited regimes from
  target-generation-limited regimes.

Required next fixes:

- Add one concise paragraph in Discussion that explains how this benchmark would
  transfer to learned detectors and real RGB-D logs.
- Keep title/abstract as benchmark/diagnostic, not policy performance.

## Reviewer 3: Related Work and Contribution

Strengths:

- Related Work now covers language-conditioned manipulation, robot benchmarks,
  RGB-D spatial target generation, and stress testing.
- Contribution is positioned as diagnostic evaluation, not SOTA manipulation.

Major risks:

- Related Work is still concise and may miss some benchmark papers depending on
  reviewer preference.
- Need to avoid implying that stress testing itself is novel in ML; the novelty
  is its controlled application to manipulation target generation with
  oracle-gap/failure logging.

Required next fixes:

- Add 2-4 more targeted citations if the final literature pass finds missing
  manipulation benchmark or VLA evaluation papers.
- Make the final contribution statement explicitly say "diagnostic benchmark"
  rather than "method".

## Devil's Advocate

Strongest counterargument:

The benchmark may be seen as an engineered simulator diagnostic using privileged
metadata rather than a language-conditioned robotic manipulation benchmark in
the full sense. If the paper claims too much, reviewers can reject it for lack
of real perception, real robot execution, and learned policy comparison.

Response strategy:

- Accept the boundary instead of fighting it.
- Say the current contribution is a reproducible diagnostic framework for
  target-selection and RGB-D target-generation failure analysis.
- Use the semantic distractor validity run to show why the diagnostic is useful:
  first-detection and query-aware selection produce large, measurable
  differences under the same stressors.
- Present real detectors, VLMs, closed-loop policies, and real robots as
  follow-on integrations, not as claims already solved.

## Submission Readiness Roadmap

Priority 1:

- Compile PDF and fix LaTeX/table/figure layout.
- Add reproducibility/config appendix or compact subsection.
- Verify every result number in the paper against generated CSVs.

Priority 2:

- Add one pipeline diagram and one stressor taxonomy figure.
- Tighten Related Work with final citation pass.
- Run full reviewer simulation on the compiled draft.

Priority 3:

- Polish abstract to stay under venue limits.
- Prepare code/data availability statement.
- Prepare cover-letter positioning for IEEE Access.
