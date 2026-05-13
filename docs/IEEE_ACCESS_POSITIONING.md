# IEEE Access Positioning Notes

## Recommended title

EmbodiedStressBench: AI-Driven Stress Testing for Language-Conditioned Embodied Manipulation

## Why IEEE Access fits

IEEE Access is suitable for a first engineering-style version because the contribution is a reproducible system, benchmark, and large-scale experimental analysis rather than a narrow theoretical result.

## Tone

Use:

- practical;
- reproducible;
- benchmark-oriented;
- diagnostic;
- engineering AI;
- simulation-based.

Avoid:

- real-world deployment claims;
- SOTA robot manipulation claims;
- "we solve embodied AI";
- overclaiming sim-to-real.

## Abstract formula

1. Problem: clean success rates hide failure mechanisms.
2. Gap: language-conditioned manipulation needs executable 3D action targets.
3. Method: stress-testing benchmark with semantic/visual/geometric/execution perturbations.
4. Metrics: success, target error, oracle gap, failure taxonomy.
5. Evidence: large-scale simulation results.
6. Limitation: no real robot; future real RGB-D validation.

## Reviewers may ask

### Q: Why no real robot?

Answer:
This work is not presented as a deployment paper. It is a controlled simulation-based stress-testing benchmark intended to isolate failure mechanisms before real-world deployment.

### Q: Is this just many perturbations?

Answer:
The contribution is not a random collection of perturbations. It is a structured diagnostic protocol that connects perturbation type, target-source quality, oracle gap, and failure taxonomy.

### Q: Why not train a new VLA?

Answer:
The paper studies evaluation and diagnosis. New VLA training can be added as a baseline, but the benchmark is model-agnostic.
