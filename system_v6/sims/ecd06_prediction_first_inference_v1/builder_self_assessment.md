# Builder Self-Assessment — ecd06_prediction_first_inference_v1

## Claim

This packet is a `scratch_diagnostic` v1 regime repair for ECD.06. It does not claim admission, canon, physics, holodeck/FEP status, a stable 3-cell invariant, or full-observability survival.

## What Changed From v0

- The v0-killer baseline is now included as `source_generator_transition_table_v0_killer_included_train_budget`.
- A `regime_validity_gate` is computed before discriminator rows.
- The primary budget is partial observability by training-data budget: 66 observed rows for 198 source+generator cells.
- Full observability is retained only as a negative control, where the table must win at adjusted error `0.0`.

## Open Risks

- The primary budget is a pinned diagnostic regime, not a general theorem about partial observability.
- The QIT-side render loop can generalize from row-local render observations; the result is only valid under the stated observation budget.
- Julia lane is a strict-carrier structural/tool guard, not an independent full recomputation of every Python row.

## Boundary

G.2a is wired from birth through `ecd06_prediction_first_inference_v1_boundary.py`, `validate_ecd06_prediction_first_inference_v1.py`, and `builder_audit_boundary_errors(...)`. This file is not an audit verdict.
