# BUILD CARD - basin_two_engine_joint_v4_within_sector_v0 (the corrected 64 target)

You are codex1 (high). Repo: `/Users/joshuaeisenhart/Codex-Ratchet`. Build everything inside `system_v6/sims/basin_two_engine_joint_v4_within_sector_v0/` (file-disjoint). NO git add/commit. FILE BOUNDARY: never write audit_verdict.md; use the builder/audit boundary helper and set the no-builder-audit-verdict gate.

## Authority

1. `40f010040`: the v4 D/R split is a Z/2 symmetry decomposition. It is not enough to count `24+24` sector duplication as genuine subsubbasins.
2. `eba5fdca0`: panel-6 q3 criterion. THE CORRECTED TARGET is genuine within-engine subsubbasins only if there is WITHIN-SECTOR splitting or IN-CLASS FLUX FLIPPING.
3. `a38a9f712` and `system_v6/sims/basin_two_engine_joint_v4_flux/`: extend the v4 machinery rather than inventing a separate graph dialect.
4. Flux estate dynamics: the state-dependent flip family is grounded in flux-continuity current signs.

## Registered Flip Family

Pin and run this small family exactly:

- `conserved_flux_control`: never flip flux. This is the control and must reproduce the v4 sector decomposition.
- `direction_sheet_opposing_current`: inherited v4 law; flip on a stage/loop boundary when the current direction sheet reaches a readout whose sign opposes engine chirality.
- `arrival_current_negative`: flip on a boundary when the arrived current/readout sign is negative.
- `arrival_current_positive`: flip on a boundary when the arrived current/readout sign is positive.
- `current_sign_change`: flip on a boundary when the pre/post readout signs differ.

## Hunt

Per realization, engine, and v3 row (`A_readout_transition_dwell`, `D_matrix64_b_order_overlay`), compute terminal/SCC structure with trapping and absent-exit proofs. A positive may be either:

- WITHIN-SECTOR terminal splitting after projecting to the flux-erased core and quotienting the global flux-sign symmetry; or
- IN-CLASS FLUX FLIPPING where a terminal SCC contains both flux values and actual flip edges.

Either outcome is honest. If no candidate survives projection and symmetry-orbit tests, report the null result.

## Controls

- Conserved-flux control: must reproduce the v4 Z/2 sector decomposition and must not count as genuine.
- Flux-erased continuity: must reproduce corrected v3 baselines exactly, A=28 and D/B-order=24.
- Order-shuffle control: run per row.
- Label permutation: counts invariant.
- Projection/symmetry test: reject full projection echoes and flux-involution sector duplicates.
- Boundary helper: use `scripts/builder_audit_boundary.py`; builder output may not author `audit_verdict.md`.

## Engineering Contract

Three engines: Julia reference via Graphs/Z3, JAX/Python, and PyTorch/PyG. Emit a standard three-engine envelope with:

- `classification="scratch_diagnostic"`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `reads_peer_result=false`
- non-empty `TOOL_MANIFEST`
- non-empty `TOOL_INTEGRATION_DEPTH`
- non-empty `TOOL_INTENT_MATRIX`
- SMT count identity with flipped expected-count controls
- positive, negative, and boundary evidence sections

End with the registered family table, the conserved-sector control, candidate result rows, projection/symmetry checks, every validator command, and status.
