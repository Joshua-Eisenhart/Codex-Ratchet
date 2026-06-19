# BUILD CARD - gcm_ratchet_order_matrix_v0

## Scope

Build `gcm_ratchet_order_matrix_v0` in this directory only. This packet is
file-disjoint and builder-owned. NO git add/commit.

Ceiling: `scratch_diagnostic`, the first measured order matrix,
carrier-and-pins-relative.

Declared axis: `order/nesting axis (cross-layer) | carve-measured | 1Q`.

## Authority Read First

- `system_v6/receipts/ratcheting_geometry_order_20260612.md`
  - Part C is the controlling measurement spec.
  - Part C sibling packet name: `ratchet_order_matrix_on_gcm_v0`.
- `system_v6/receipts/ratchet_geometry_order_hypothesis_20260612.md`
  - Candidate rule: `X_{n+1} = {x in X_n : condition_n(x)}`.
- Committed ratchet fragments and mode-4 packets provide regression anchors,
  not new promotion authority.
- `system_v6/receipts/audit_standards_codex_v1.md`
  - G.2a applies from birth.
- `scripts/gcm_substrate_check.py`
  - Positive substrate helper must pass.
  - Lineage-free negative must fail red.

## Substrate-First Stop Rule

Required frozen object:

- `gcm_object_id`: `gcmobj_a40e54e13cec01466c9d675028b3574b`
- `registry_body_sha256`:
  `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`

If frozen carved IDs are unavailable, report:

`blocked_no_frozen_gcm_substrate`

The IDs exist in the registry, so this build is unblocked. The packet must also
write and validate:

- a positive payload accepted by `scripts/gcm_substrate_check.py`;
- a lineage-free negative rejected by the same helper;
- a wrong-substrate negative rejected by the same helper.

## Packet Contract

Measure the order matrix on the frozen carved object. Do not declare a total
ladder. Every step is typed as domain -> codomain on the survivor/lineage
structure.

Step alphabet pinned for this packet:

1. shell conditioning: restrict to the occupied `T_eta = pi/4` stratum;
2. phase/density quotient;
3. brickwork local update: the pinned A/B local update feedstock, by source hash;
4. channel applications: `D_z`, `R_x` through committed fixtures;
5. flux/holonomy locking: record strip values, then require them.

For every ordered pair `(step_i, step_j)`:

- apply both orders to the carved object;
- compute survivor-set symmetric difference;
- compute witness-set symmetric difference;
- classify honestly:
  - `COMMUTES_ORDER_FREE`: honest null, order-free;
  - `NONCOMMUTES_NUMERIC` or `DIRECTIONAL_ENABLE`: ordered finding;
  - `NONCOMMUTES_MORTALITY`: one order dies and names the missing object;
  - `NOT_COMPARABLE`: both orders die under missing required objects.

Honest null rule: a commuting pair is order-free, never forced.

Honest death rule: a dying pair reports the named mortality class and missing
object, never a numeric gap.

## Required Controls

C6 controls are required:

- label shuffle;
- reversed order;
- quotient-erasure;
- missing-layer/source-target failure;
- wrong-substrate lineage;
- local-only replacement;
- commuting-pair zero control;
- mortality replay;
- depth ablation;
- entropy/readout ablation.

This build also records the lineage-free negative because the substrate helper
is a hard local gate.

## G.2a Boundary

Use `scripts/builder_audit_boundary.py` from birth through
`gcm_ratchet_order_matrix_v0_boundary.py`.

The builder writes build artifacts only. It does not write `audit_verdict.md`.
Validators check the build-time field `no_builder_audit_verdict`; they do not
require permanent absence of a later independent read-only audit.

Allowed writes:

- this `build_card.md`;
- `gcm_ratchet_order_matrix_v0_common.py`;
- `gcm_ratchet_order_matrix_v0.py`;
- `gcm_ratchet_order_matrix_v0_boundary.py`;
- `validate_gcm_ratchet_order_matrix_v0.py`;
- `builder_self_assessment.md`;
- `tests/test_gcm_ratchet_order_matrix_v0.py`;
- files under `results/` for this packet only.
