# Build Card - gcm_constraint_carve_3q_v0

Status: build packet for the QIT floor rung of the GCM constraint carve.
Claim ceiling: `scratch_diagnostic`; carrier-and-pins-relative; not THE manifold.
Write scope: `system_v6/sims/gcm_constraint_carve_3q_v0/` only, including generated result JSONs under `results/`.
Git boundary: NO git add/commit.

DECLARE: layers 1-2 (+17 tensor) | carve | 3Q.

## Authority

Read-first authority:

1. 1Q substrate registry:
   - `system_v6/sims/gcm_object_id_freeze_v0/results/gcm_object_id_freeze_v0_registry.json`;
   - `gcm_object_id=gcmobj_a40e54e13cec01466c9d675028b3574b`.
2. 2Q carve and conditional 2Q registry:
   - `system_v6/sims/gcm_constraint_carve_2q_v0/`;
   - `system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_registry.json`;
   - 2Q audit remains conditional/in-flight for registry cleanliness, so this packet consumes it only as scratch feedstock.
3. Existing 3Q feedstock, consumed not rebuilt:
   - `geo_s1_three_qubit_floor_exact_v0` at commit hint `6ed5e961e`;
   - `stage_lifted_spinor_shell_n3_v0` at commit hint `3a53d16af`;
   - climb-ledger correction `f7b0ee5fe`, `system_v6/receipts/qubit_ladder_climb_ledger_20260612.md`.
4. Standards codex:
   - `system_v6/receipts/audit_standards_codex_v1.md`.

## Active Coordinates

- layer: `layers 1-2 (+17 tensor)`;
- nesting: `carve`;
- qubit depth: `3Q`.

## Candidate Space

Pinned 3Q candidate family:

1. `2q_survivor_product_lift`: every 2Q survivor from `gcm_constraint_carve_2q_v0` tensored with the pinned third-qubit control `|0><0|`.
2. `entangled_boundary_anchor`: eight named 3Q floor/shell anchors, including standard GHZ/W representatives, biseparable and product controls, one invalid density control, and one locally rotated generalized-GHZ anchor with active first-qubit probes.

C1-C3 are unchanged in form and instantiated at 3Q through the first-qubit local adapter. Entanglement, CKW, Cl(6), and shell support are downstream rows, not inputs to C1-C3.

## Active Constraint Source Lines

C1 predicate source line: `C1_finite_3q_density_carrier` accepts exactly finite 3Q candidates whose pinned construction is trace-one positive semidefinite on the `C^8` density carrier.

C2 predicate source line: `C2_probe_distinguishability_xz_local_adapter_pin` accepts exactly candidates whose active first-qubit probe pair `(2*Tr((sigma_x tensor I tensor I)rho), 2*Tr((sigma_z tensor I tensor I)rho))` is not `(0, 0)`.

C3 predicate source line: `C3_persistence_n01_order_gap` accepts exactly candidates whose first-qubit `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ.

## Required Structure

Packet structure:

1. pin 1Q registry, conditional 2Q registry, and existing 3Q floor/shell feedstock;
2. declare the finite 3Q candidate family and active C1-C3 predicates;
3. compute `M(C)` at 3Q;
4. emit the kill ledger;
5. build the probe quotient `S/~_M`;
6. run existence probes and controls;
7. compute cross-rung product embedding and partial-trace rows against the 2Q survivors;
8. compute the CKW monogamy row on entangled 3Q survivors;
9. emit floor rows showing which Cl(6)/C^8 and n3 shell-support structure the carved set carries;
10. answer whether C1-C3 distinguish GHZ and W.

Controls:

- empty-C;
- cliff/overconstrained-C;
- erasure-bite per constraint;
- probe-scramble;
- source-recompute terrain-blindness guard;
- injection-red validator;
- lineage-free negative red;
- 1Q and 2Q regressions.

## Expected Result

Under C1-C3:

- candidate count: `552`;
- product embedding candidates from 2Q: `544`;
- entangled boundary anchors: `8`;
- survivor count: `545`;
- quotient class count: `9`;
- lifted 2Q product survivors: `544`;
- tripartite entangled survivor anchors: `1`;
- standard GHZ killed by C2;
- standard W killed by C3;
- locally rotated generalized-GHZ anchor survives and satisfies CKW with margin `0.1875`;
- classification: `scratch_diagnostic`;
- `promotion_allowed=false`;
- `formal_admission_allowed=false`.

## G.2a Boundary

This packet uses `scripts/builder_audit_boundary.py` from birth. The builder does not write `audit_verdict.md`; if a later independent audit creates one, the validator accepts it only through the shared independent/fresh/read-only header gate.
