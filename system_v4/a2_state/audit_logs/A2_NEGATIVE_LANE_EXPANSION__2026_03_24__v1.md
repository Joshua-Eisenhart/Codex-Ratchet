# A2 Negative Lane Expansion (v1)

## Purpose

Deepen the falsifier side of the system by:
- promoting dormant negative SIMs into the live runner
- promoting dormant axis-0 orthogonality probes into the live runner
- adding a new 3-axis orthogonality sweep so the system is no longer limited to pairwise-only axis checks

## Changes Landed

### Newly promoted into `run_all_sims.py`

Negative / graveyard:
- `neg_scrambled_sequence_sim.py`
- `neg_inverted_major_loop_sim.py`

Axis orthogonality:
- `orthogonality_axis0_axis1_sim.py`
- `orthogonality_axis0_axis2_sim.py`
- `orthogonality_axis0_axis4_sim.py`
- `orthogonality_axis0_axis5_sim.py`
- `orthogonality_axis0_axis6_sim.py`

### Newly added

- `axis_triplet_orthogonality_sim.py`

This new SIM tests all `C(6,3) = 20` axis triplets across `d in {4, 8}` and emits one evidence token per triplet:
- `PASS` if the triplet retains rank-3 independence
- `KILL` with `TRIPLET_RANK_COLLAPSE` if the triplet is rank-deficient or catastrophically ill-conditioned

## Live Outcome After Expansion

Direct rerun of `system_v4/probes/run_all_sims.py` produced:
- `186` total tokens
- `153` PASS
- `33` KILL

Compared to the prior clean synchronized floor:
- previous: `159 / 138P / 21K`
- current: `186 / 153P / 33K`

This is not a generic regression. Most of the additional KILLs are intentional graveyard boundaries becoming visible.

## Healthy New Graveyard Signals

These newly counted surfaces KILL exactly as intended:
- `neg_scrambled_sequence_sim.py` → `RANDOM_SEQUENCE_STALLS`
- `neg_inverted_major_loop_sim.py` → `INVERTED_MAJOR_LOOP_HEATS`

These newly counted orthogonality confirmations PASS:
- `orthogonality_axis0_axis1_sim.py`
- `orthogonality_axis0_axis2_sim.py`
- `orthogonality_axis0_axis4_sim.py`
- `orthogonality_axis0_axis5_sim.py`
- `orthogonality_axis0_axis6_sim.py`

## New Structural Warning

`axis_triplet_orthogonality_sim.py` emitted:
- `10 PASS`
- `10 KILL`

All observed triplet KILLs involved `A3_Chirality`.

Killed triplets:
- `A1_Coupling x A2_Frame x A3_Chirality`
- `A1_Coupling x A3_Chirality x A4_Variance`
- `A1_Coupling x A3_Chirality x A5_Texture`
- `A1_Coupling x A3_Chirality x A6_Precedence`
- `A2_Frame x A3_Chirality x A4_Variance`
- `A2_Frame x A3_Chirality x A5_Texture`
- `A2_Frame x A3_Chirality x A6_Precedence`
- `A3_Chirality x A4_Variance x A5_Texture`
- `A3_Chirality x A4_Variance x A6_Precedence`
- `A3_Chirality x A5_Texture x A6_Precedence`

Interpretation:
- pairwise orthogonality is not enough
- chirality appears to be the fragile axis under 3-axis composition
- this is the best current candidate for deeper axis-law repair work

## What This Expansion Achieved

1. The graveyard is less ad hoc and more executable.
2. The system now has live coverage for sequence-order falsification, not just operator-ablation falsification.
3. Axis orthogonality is now checked at:
- pairwise level
- axis0 cross-axis level
- triplet level

## Next Best Builds

1. Add `orthogonality_axis0_axis3_sim.py` if the missing Axis0 x Chirality surface is still absent.
2. Build a dedicated `axis3_chirality_repair_sim.py` or `axis3_triplet_isolation_sim.py` to explain why `A3` is collapsing across so many triplets.
3. Add another manifold-derived graveyard battery for remaining cross-cutting properties that still rely on weak or legacy coverage.
4. Regenerate downstream surfaces if controller docs need to reflect the new `186 / 153 / 33` state.
