# Build Card - gcm_constraint_carve_v1

Status: terrain-blind repair of `gcm_constraint_carve_v0`.
Claim ceiling: `scratch_diagnostic`; first-carve-candidate v1 only; carrier-and-pins-relative; not THE manifold.
Write scope: `system_v6/sims/gcm_constraint_carve_v1/` only, including generated result JSONs under `results/`.
Git boundary: NO git add/commit.

## Authority

Read-first authority:

1. `system_v6/sims/gcm_constraint_carve_v0/audit_verdict.md`
2. `system_v6/receipts/gcm_reanchor_requirement_20260612.md` at `393c5147a`
3. `system_v6/receipts/audit_standards_codex_v1.md`
4. `system_v6/sims/gcm_constraint_carve_floor_v0/` as prior art only; cite nothing from it as authority.

## v0 Repair Contract, Verbatim

Next admissible repair:

1. Split C4 out of the admissibility carve or rewrite it as a terrain-blind, source-pinned constraint with a literal cited predicate.
2. Add a real no-identity-leak independence probe and required `identity_leak_*` fields.
3. Repair C2 citation so the exact x/z probe and zero-active-class exclusion are sourced or explicitly demoted as a local adapter pin.
4. Keep terrain readout as a downstream post-carve analysis that cannot affect survival.
5. Track the packet, then rerun normal live validators under an explicit write plan.

## v1 Choice

v1 takes the first branch of repair item 1: C4 is split out of the admissibility carve. The active survival constraints are C1-C3 only. v0 C4 is rerun only as a regression comparison row, where it is explicitly marked as a rejected terrain-framed variant.

The downstream terrain readout is post-carve analysis only. It must not change `Adm_C`, survivor count, kill ledger, quotient class count, controls, or `M(C,t)`.

## Active Constraint Source Lines

These local adapter pins are the literal executable predicates for v1. They are local packet pins, not owner-source-derived theorem statements.

C1 predicate source line: `C1_finite_density_carrier` accepts exactly candidates on `GRID_VALUES={-1,-1/2,0,1/2,1}` with `x*x + y*y + z*z <= 1`.

C2 predicate source line: `C2_probe_distinguishability_xz_local_adapter_pin` accepts exactly candidates whose active probe pair `(2*x, 2*z)` is not `(0, 0)`.

C3 predicate source line: `C3_persistence_n01_order_gap` accepts exactly candidates whose `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ.

C5 predicate source line: `C5_t1_positive_active_coordinate_pin` is a downstream `M(C,t)` hook that keeps candidates whose first nonzero active coordinate in `(x, z)` is positive.

## Required Structure

Packet structure follows v0:

1. pin C;
2. compute `M(C)`;
3. emit the kill ledger;
4. build `S/~_M`;
5. run the four existence probes;
6. read carved structure downstream;
7. run the `M(C,t)` step.

Added v1 requirements:

- no terrain/atlas/engine-family terms inside active admissibility predicates;
- a blindness control injects a deliberately terrain-framed variant, and the packet guard must catch it;
- no-identity-leak independence emits `identity_leak_detected`, `identity_leak_excluded_best_accuracy`, and `identity_leak_exclusion_rule`;
- the v0 regression row recomputes v0 under the failed C4 and reports which survivors/classes changed.

## Expected v1 Result

Under C1-C3:

- candidate count: 125;
- density subcarrier count: 33;
- survivor count: 16;
- quotient class count under x/z probes: 8;
- v0 regression with the rejected C4: 8 survivors and 4 quotient classes;
- controls: empty-C, over-constrained cliff, per-constraint erasure bite, probe scramble, and blindness control all fire;
- envelope mode: `all_three_full_sims`;
- classification: `scratch_diagnostic`;
- `promotion_allowed=false`;
- `formal_admission_allowed=false`.

## G.2a Boundary

This packet uses `scripts/builder_audit_boundary.py` from birth. The builder does not write `audit_verdict.md`; if a later independent audit creates one, the validator accepts it only through the shared independent/fresh/read-only header gate.
