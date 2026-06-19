# Builder Self-Assessment - manifold_ab_weld_relation_v0

Status: builder-side self-assessment only. This is not an independent audit verdict.

## Scope Built

- Separate Family A and Family B state objects are loaded from committed result envelopes by SHA-256 and kept as separate `pinned_state_objects`.
- The coordinate map classifies each packet coordinate as `shared`, `related`, or `independent`, with computed classification fields.
- Weld-only rows are computed only after A and B are jointly bound through the coordinate map.
- Non-recoverability is computed by erasing A, erasing B, and erasing both; each weld-only row becomes not recoverable.
- Cross-family controls compute scoped movement tables for A-only, B-only, weld-only, and no-input perturbations.
- z3 and cvc5 bind measured A values, measured B values, and the weld relation. Valid mismatch polarity is `unsat`; erased and perturbed flips are `sat`.

## Boundaries

- Classification is `scratch_diagnostic`.
- `promotion_allowed` is false.
- `formal_admission_allowed` is false.
- Family C is a fence-check citation only, not a weld input.
- This packet does not claim manifold, axis, bridge, physics, or charts-on-surface admission.
- The committed v2 weld remains caveated chart-to-chart bookkeeping context; this packet only fills the relation-level gap rows named by the feedstock inventory.

## G.2a Boundary

The packet validator and tests use `scripts/builder_audit_boundary.py` for the audit-boundary check. They do not hard-code permanent absence of `audit_verdict.md`, so a later independent audit can be added without breaking the builder packet solely because the audit file exists.
