# BUILD CARD - gcm_ratchet_order_matrix_v1

## Scope

Build `gcm_ratchet_order_matrix_v1` in this directory only. This packet is
file-disjoint and builder-owned. NO git add/commit.

Ceiling: `scratch_diagnostic`, carrier-and-pins-relative.

Declared axis: `order/nesting axis | carve-measured | 1Q`.

## Packet Contract

This is the full Part-C alphabet extension at 1Q over the frozen GCM object
`gcmobj_a40e54e13cec01466c9d675028b3574b`.

Alphabet:

1. `S` shell/leaf conditioning;
2. `Q` quotient/lens equivalence;
3. `W` local window/support restriction;
4. `F` flux locking / connection-holonomy recomputation;
5. `T` terrain conditioning from committed S5/S6 conditioned-flow machinery;
6. `O` operator residency/precedence as channel-application typing;
7. `D` depth ladder climb as the committed 1Q-to-2Q cross-rung embedding.

True carved StageRegion operator residency remains `blocked_no_realization` and
is reported as a blocked component, not faked as an admitted step.

## Required Checks

- Pass `scripts/gcm_substrate_check.py` on the positive payload.
- Keep the lineage-free negative red.
- Keep the wrong-substrate negative red.
- Reproduce the v0 20 off-diagonal regression rows from commit `ec648675d`.
- Keep `D` reserved for depth; do not reuse it for channels.
- Run executable C6 controls at birth.
- Validate G.2a with `gcm_ratchet_order_matrix_v1_boundary.py`.

Allowed writes: this packet directory and its `results/` directory only.
