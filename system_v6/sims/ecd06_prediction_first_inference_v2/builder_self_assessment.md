# Builder Self-Assessment - ecd06_prediction_first_inference_v2

## Claim

This packet is a `scratch_diagnostic` equal-information ECD.06 test. It asks whether a learned prediction-error-correction loop structure beats equally informed one-shot predictors on the committed v1 edge carrier.

It does not claim admission, canon, physics, holodeck/FEP status, a stable 3-cell invariant, or full-observability survival.

## What Changed From v1

- The QIT side no longer reads held-out `render` vectors.
- The QIT side keeps only the loop structure: learned render proposal, learned residual error, and one correction update fit from the same training budget as baselines.
- `information_parity_gate` enumerates training, prediction, evaluation-only, and forbidden inputs for both sides before discriminator rows.
- The v1 render-access equalizer is retained only as a negative control and must reproduce the `0.344150808264` tie.

## Open Risks

- The primary budget is a pinned diagnostic regime, not a theorem about all partial-observability budgets.
- The learned loop policy class is one explicit architecture family; a different loop learner could change the result.
- Julia is a strict-carrier structural/tool lane, not an independent full recomputation of every Python row.

## Boundary

G.2a is wired from birth through `ecd06_prediction_first_inference_v2_boundary.py`, `validate_ecd06_prediction_first_inference_v2.py`, and `builder_audit_boundary_errors(...)`. This file is not an audit verdict.
