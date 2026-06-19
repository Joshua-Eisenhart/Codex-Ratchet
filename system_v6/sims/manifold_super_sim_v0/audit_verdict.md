# manifold_super_sim_v0 Audit Verdict

Bottom line: `GENUINE-WITH-CAVEATS`, not a clean full-card pass.

This is not a cherry-picking script wearing an integration costume. The decisive L1/L2/L4 rows are rebuilt from the shared 33-cell finite object and pinned S4/S5 generator rows; L3 recomputes its information rows from pinned S4/readout rows; L5 assembles a typed ledger from the recomputed L3/L4 rows plus parent type conventions. The weld anchors and controls rerun green.

It is also not future-citable as a fully clean "first integrated run" yet. The source-hash locks point at parent `audit_verdict.md` files instead of the consumed result JSONs, the trajectory artifact lacks the unified-run per-step `step-dependent` versus `carried` classification, reduced G1 L4 rows drop chart-relative labels, and the all-three-engine independence claim is stronger than the code path.

## Verdict

`VERDICT: GENUINE-WITH-CAVEATS`.

Accepted claim:

`manifold_super_sim_v0` is a scratch-diagnostic Family A integrated run over one shared 33-cell Bloch-grid object. It recomputes finite basin, chart-control, information, fusion, and ledger rows against that object and preserves the no-promotion ceiling.

Rejected above ceiling:

Do not cite it as formal admission, canonical process truth, an invariant manifold theorem, bridge/axis/physics evidence, a two-engine/joint-engine convention result, or a fully independent all-three-backend implementation of L1-L5.

## Recompute Reality

Fresh independent recomputation from the current pinned S4/S5 result rows rebuilt the finite transition graphs without reading parent graph rows:

- `G0 transition_graph_sha256 = bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0`.
- `G1 terminal_class_sizes = [1, 14, 18]`.
- `G1 transition_graph_sha256 = 38388af4497894e6e88f11de6f9ec633235f26753d2c657ff8f360b3ce15871d`.
- In-memory `D_z M[0][0] += 0.05` changed `G0` to `898b8ee7cc3e8948d31d0eb9d7af556475b1b6b737b555a785169813c7b22912`.

Source trace:

- `rebuild_sweep()` calls `sweep_common.load_all_generators(expm_fn)`, recomputes S5 `exp(hA)` at `h=1/2`, builds graphs, then compares G0 to the parent only as an anchor.
- No parent raw transition graph is imported on the L1 claim path.
- Parent result JSONs are still read for pinned S4/S5 rows, S4/readout information rows, z4 co-citation, and parent ledger type conventions. That is allowed as source/citation use, but the hash-lock surface is wrong as described in `G1`.

## Weld Anchors

All required anchors matched on fresh inspection:

- `G0` SHA matched `bd0cd3b5...`.
- `G1` partition was `[1, 14, 18]` with `may_basin_sizes == must_basin_sizes == [1, 14, 18]`.
- L2 recomputed 2x and 3x refinements at 3 terminal classes and the pinned non-axis rotated chart at 2 terminal classes.
- `D_z` six-state Holevo was `0.411341122022618`; killed information was `0.28180605853732726`.
- Stage-word endpoint was `0.0932927444282512`.
- Fusion G1 merge controls gave erased record `0`, partial record `ln(2)`, full record `ln(3)`, and z4 erased/partial co-citation.
- z3 and cvc5 SMT rows bind computed terminal counts and return identity `UNSAT` with erased/perturbed `SAT` flips.

## Controls

Controls mostly fire as real computations:

- Stale-import control: in-memory `D_z` perturb changed both `G0` graph hash and `D_z` Holevo (`0.411341122022618 -> 0.4266540975391361`).
- Order-shuffled control changes the actual R_C trajectory.
- Root-off and similarity-only controls reject basin language without dynamics.
- Quotient-erased control degrades the may/must object.
- Decorative-layer detector covers L1-L5, but with caveat `G5`: L5 is guarded by a deliberate cross-type flag, not a recomputed L5 input mutation.

## Named Caveats

`G1_SOURCE_HASH_LOCKS_ARE_WRONG_SURFACE`: `source_locks()` merges `PARENT_RESULTS` and `AUDIT_VERDICTS` under the same keys, so audit verdict paths override consumed result JSON paths. The emitted `parent_hash_pins`, `stability_pairs`, and `state_object_id` lock the parent audit files for S4/S5, not the actual S4/S5 result JSONs being consumed.

`G2_G1_CHART_LABELS_DROPPED_IN_REDUCED_ROWS`: the source fusion object carries chart-relative labels, but `layer_l4_fusion()` strips them from reduced `terminal_class_restricted_throughput` and `basin_conditioned_may_must_flow` rows. Standalone citation of those reduced G1 rows would violate the chart-relative discipline.

`G3_UNIFIED_TRAJECTORY_CLASSIFICATION_MISSING`: the trajectory artifact is SHA-verified and uses one `state_object_id`, but it is a layer-signature summary, not the `manifold_unified_run_v0` mechanism with per-step row classifications as `step-dependent` versus `carried`.

`G4_BACKEND_INDEPENDENCE_SCOPE`: Julia independently rebuilds/checks G0/G1 graph counts with Graphs/Z3, while JAX and PyTorch both call the shared Python common builder for the full L1-L5 object. PyTorch/JAX package probes are source-backed, but they are not independent full-object implementations.

`G5_DECORATIVE_LAYER_DETECTOR_WEAK_ROWS`: L1, L3, and L4 have direct perturbation/change checks. L2 uses a live chart variation control. L5 relies on a type-mixing flag rather than an input-perturbed recomputation of an L5-owned row.

`G6_PARENT_CAVEATS_CARRIED`: current S4/S5 pinned rows are consumable for this run and current S5 Ne rows are nonzero, but this packet does not close parent scientific caveats. It consumes pinned source tables at scratch ceiling.

`G7_UNTRACKED_PACKET`: `git status --short -- system_v6/sims/manifold_super_sim_v0` reports the packet as untracked in this checkout. This audit verifies current filesystem state only. No `git add` or commit was run.

## Verification

Commands/checks rerun:

- Imported packet validator without writing validator results: `ok=true`, `errors=[]`.
- `scripts/validate_three_engine_sim_result.py --require-pytorch ...`: `ok=true`.
- `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed ...`: `ok=true`.
- `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent ...`: `ok=true`.
- Trajectory artifact SHA sidecar recomputed: `c8013d9f0ff626bf102f3325dbcddbb8d16a59fb01e6518c3dfb6f94a4504c50`, `ok=true`.
- Pytest suite rerun in a temporary repo-shaped copy to preserve the live write boundary: `4 passed, 5 subtests passed`.

No live packet result JSON was intentionally rewritten during this audit.

## Future-Citation Rule

Allowed citation:

`manifold_super_sim_v0` is a scratch-diagnostic Family A integrated run that recomputes the G0/G1 basin graph anchors, chart controls, S4 information rows, G1 fusion record/throughput/flow rows, and typed ledger rows over one shared 33-cell Bloch-grid object, with weld anchors and validators green.

Required citation suffix:

`Use with caveats G1-G7: result-source hashes are not correctly locked, reduced G1 L4 rows need chart labels, the trajectory lacks per-step step-dependent/carried classification, and backend independence is partial.`

Forbidden citation:

Do not cite this as formal admission, canonical manifold proof, invariant/frame-independent sub-basin geometry, axis/bridge/physics evidence, two-engine convention evidence, or full independent Julia/JAX/PyTorch recomputation of L1-L5.

## Super-Sim v1 Must Add

1. Hash-lock the actual consumed result JSONs and pinned row subhashes for S4/S5, z4, ledger, throughput, fusion, and unified-run parents; do not let audit verdict paths override result-source locks.
2. Persist a richer trajectory artifact with per-step rows, per-row input signatures, and explicit `step-dependent` versus `carried` classification.
3. Preserve chart-relative labels in every reduced G1 row, especially terminal-class throughput and basin-conditioned flow rows.
4. Replace L5's decorative detector with an actual L5 input perturbation that changes an L5-owned row signature.
5. Either implement independent JAX/PyTorch/Julia L1-L5 carriers or downgrade the envelope mode to the honest shared-common scope.
6. Add Julia `state_object_id` and stronger Julia coverage beyond G0/G1 counts if the envelope keeps `all_three_full_sims`.
7. Re-instantiate Family B as its own integrated object, not as a citation folded into Family A.
8. Add two-engine/joint-engine rows only after the convention program admits them.
9. Carry or repair parent S4/S5 caveats explicitly in the build card and result boundary.

## Closure Annotation - Hardening 42542f120 Round 1

`G1_SOURCE_HASH_LOCKS_ARE_WRONG_SURFACE`: `CLOSED_BY_HARDENING_42542f120_ROUND_1`.

Closure evidence: the hardening round changed `source_locks()` to lock consumed result JSONs rather than parent `audit_verdict.md` paths. The current result-source lock surface is the consumed result surface.

`G2_G1_CHART_LABELS_DROPPED_IN_REDUCED_ROWS`: `CLOSED_BY_HARDENING_42542f120_ROUND_1`.

Closure evidence: the hardening round preserved `G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE` in the reduced L4 G1 rows.

Updated required citation suffix:

`Use with caveats G3-G7: the trajectory lacks per-step step-dependent/carried classification, backend independence is partial, L5's decorative detector is weaker than a direct L5 input perturbation, parent caveats are carried, and tracking status must be cited from the current commit/worktree state.`
