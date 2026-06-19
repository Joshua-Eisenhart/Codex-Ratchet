# BUILD CARD - ring_checkerboard_qca_v3

## Boundary

Build in `system_v6/sims/ring_checkerboard_qca_v3/` only. No git add. No git commit.

## Authority

- `315ac529c`: CA doctrine v3 rule. The L/R engines must enter as distinct local unitaries realizing committed engine dynamics, not as shift operators under flux labels. Any engine row numerically equal to a calibration row is self-rejecting.
- `0015b410d`: v2 extraction fixture earned. Reuse the open-chain crossing-rank machinery verbatim; the rejected part was the L/R engine construction, not the extraction method.
- `fe06d49bd`: classical floor. The alternating/deductive and paired/inductive phase disciplines are committed as structurally distinct local dynamics.
- Panel 8: keep the finite-ring caveat and the standard-math index boundary. Do not claim a nontrivial finite-ring automorphism-class index.

## Build

Realize the committed two-loop engine dynamics as open-chain brickwork local unitaries:

- `engine_L_flux_IN_left_O1`: left-moving open-chain shift composed with the alternating/deductive brickwork pattern. The O1 flux sign enters as negative relative phase and left direction.
- `engine_R_flux_OUT_right_O1`: right-moving open-chain shift composed with the paired/inductive brickwork pattern. The O1 flux sign enters as positive relative phase and right direction.

The brickwork layer must be a real local unitary circuit, not metadata and not a pure shift. Then extract the indices with the v2 crossing-rank machinery.

## Required Gates

- Calibrations still compute `+1`, `-1`, and `0` from realized operators.
- The L/R engine rows must be numerically distinct from every same-shape calibration row; equality is `SELF_REJECTING`.
- The L/R engine rows may honestly produce opposite nonzero indices or zero/equal indices. Opposite nonzero earns expectation 2 for this open-chain fixture; zero/equal means the committed engine flux is not index-visible under this probe.
- Gauge row recomputes ranks after a real local unitary insertion.
- Index-0 controls remain non-distinguishing.
- The falsifier replaces the R engine with the L brickwork/direction and must kill the opposite-sign predicate.
- Periodic ring closure rows stay finite-ring trivial.

## Standard Contract

Emit `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, non-empty `TOOL_MANIFEST`, non-empty `TOOL_INTEGRATION_DEPTH`, honest `TOOL_INTENT_MATRIX`, positive/negative/boundary sections, three engine results, envelope, packet-local validator result, and focused pytest coverage.
