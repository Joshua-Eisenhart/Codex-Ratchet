# Builder Self-Assessment -- engine_16_stage_definition_correspondence_v0

This is builder prose, not an independent audit verdict.

## What Was Built

- A file-disjoint scratch packet under `system_v6/sims/engine_16_stage_definition_correspondence_v0/`.
- Sixteen explicit macro-stage maps on the one-qubit Bloch/density carrier.
- Per-stage matrices, geometry rows, entropy/purity effects, eng64-family fingerprints, a full 16x16 correspondence matrix, a 16x16 non-equivalence matrix, and killable controls.
- Three engine lanes plus a `three_engine_sim_result_v1` envelope and packet validator.

## Builder Result

- Correspondence result: `MISMATCH`.
- The convention-pinned 16 defined rows collapse to 12 label-free behavior components.
- Exact matches against the discovered `eng64_stage_fingerprint_ids_v0` component set: 0 of 16.
- Order-erased control collapses to 8, chirality-erased L/R pairs merge, scrambled assignments do not improve correspondence, and identity stages collapse to 1.

## Boundaries

- The definitions are a convention-pinned proposal, not engine-stage admission.
- The `R_x/D_z` values are carried as fixtures, not canonical stage math.
- The substage convention remains unpinned.
- Either correspondence outcome is accepted as the result; the builder does not tune definitions after seeing the match matrix.
- G.2a is wired from birth through `engine_16_stage_definition_correspondence_v0_boundary.py` and `scripts/builder_audit_boundary.py`.

## Claim Ceiling

Accepted ceiling: `scratch_diagnostic`, specifically `macro_stage_definition_correspondence_proposal_only`.

Blocked consumers: Matrix64 admission, QIT-engine admission, axis admission, bridge/manifold/physics claims, and any engine-stage unlock.
