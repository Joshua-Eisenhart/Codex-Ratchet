# Build Card - gcm_constraint_carve_2q_v0

Status: build packet for the ladder's second rung for the carve itself.
Claim ceiling: `scratch_diagnostic`; carrier-and-pins-relative; not THE manifold.
Write scope: `system_v6/sims/gcm_constraint_carve_2q_v0/` only, including generated result JSONs under `results/`.
Git boundary: NO git add/commit.

DECLARE: layers 1-2 | carve (order B) | 2Q.

## Authority

Read-first authority:

1. Twice-audited 1Q carve: `system_v6/sims/gcm_constraint_carve_v1/`.
2. 1Q authority hashes carried into this packet:
   - common source: `96d80d6f273a017a0cc80333c94fff0cf6b03bbe406f0a29dc69ccbc6dcb18db`;
   - result: `ca6ae0277e4a5c77044b1075626262e6bfdab4c99f818e85abc123322f74b756`;
   - envelope: `450ecaba6c77756688d0dc3cae2b3032170b3bead159b914b0e1c6de55ccae6d`.
3. Freeze registry for cross-rung lineage:
   - `system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json`;
   - registry hash `64cd715166cee039f89494166496adabf15300bae4b8cc79fee98fc0251189f2`.
4. Layer-stack supplement 1:
   - `system_v6/receipts/gcm_layer_stack_reference_20260612.md`.
5. Standards codex:
   - `system_v6/receipts/audit_standards_codex_v1.md`.

## Active Coordinates

- layer: `layers 1-2` (constraint set plus carved object `M(C)+S/~_M`);
- nesting: `carve (order B)`;
- qubit depth: `2Q`.

## Candidate Space

Pinned 2Q candidate family:

1. `product_grid`: all ordered pairs of 1Q Bloch-grid coordinate candidates over `{-1,-1/2,0,1/2,1}^3`, interpreted as `rho_A tensor rho_B`.
2. `bell_diagonal_grid`: all diagonal Pauli-correlation candidates `1/4*(II + cx XX + cy YY + cz ZZ)` over the same grid.
3. `purification_boundary`: one Schmidt-purification candidate for each 1Q density-grid first marginal, with `partial_trace_A` pinned to that first marginal.

C1 selects the density subcarrier from this finite trace-one candidate family. Entanglement is a post-carve/boundary readout only; it is not an input to C1-C3.

## Active Constraint Source Lines

These are the literal 2Q instantiations of the same C1-C3 forms from the 1Q carve.

C1 predicate source line: `C1_finite_2q_density_carrier` accepts exactly finite 2Q candidates whose pinned construction has trace one and nonnegative spectrum under its family eigenvalue rule.

C2 predicate source line: `C2_probe_distinguishability_xz_local_adapter_pin` accepts exactly candidates whose active first-qubit probe pair `(2*Tr((sigma_x tensor I)rho), 2*Tr((sigma_z tensor I)rho))` is not `(0, 0)`.

C3 predicate source line: `C3_persistence_n01_order_gap` accepts exactly candidates whose first-qubit `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ.

C5 predicate source line: `C5_t1_positive_active_coordinate_pin` is a downstream `M(C,t)` hook that keeps candidates whose first nonzero active first-qubit coordinate in `(x, z)` is positive.

## Required Structure

Packet structure:

1. pin the finite 2Q candidate family and active C1-C3 predicates;
2. compute `M(C)` at 2Q;
3. emit the kill ledger;
4. build the probe quotient `S/~_M`;
5. run the four existence probes: stability, no-identity-leak independence, chart recovery, negative controls;
6. read carved structure downstream;
7. compute the cross-rung product/partial-trace row against the pinned 1Q carve and freeze registry;
8. compute the 2Q boundary phenomena row and the kill ledger diff vs 1Q;
9. run `M(C,t)`.

Controls:

- empty-C;
- over-constrained-C;
- per-constraint erasure bite;
- probe-scramble;
- source-recompute terrain-blindness guard with injection-red control;
- 1Q regression and hash lock.

## Expected Result

Under C1-C3:

- candidate count: `15783`;
- density subcarrier count: `1167`;
- survivor count: `544`;
- quotient class count under first-qubit x/z probes: `8`;
- product survivors: `528`;
- entangled survivors: `16`;
- `M(C,t)` survivors: `272`;
- 1Q product/control embedding count: `16`;
- partial-trace image equals the pinned 1Q survivor set;
- Bell-diagonal valid entangled candidates enter the 2Q space but are killed by C2 under the local x/z probe pin;
- envelope mode: `all_three_full_sims`;
- classification: `scratch_diagnostic`;
- `promotion_allowed=false`;
- `formal_admission_allowed=false`.

## Seven Audit Questions

The result and envelope must answer all seven audit questions:

1. Which layer?
2. Which nesting relation?
3. Which qubit depth?
4. Which surface/network?
5. Which three engines ran?
6. Which entropy/readout families varied?
7. What broke when depth/nesting/surface was removed?

## G.2a Boundary

This packet uses `scripts/builder_audit_boundary.py` from birth. The builder does not write `audit_verdict.md`; if a later independent audit creates one, the validator accepts it only through the shared independent/fresh/read-only header gate.
