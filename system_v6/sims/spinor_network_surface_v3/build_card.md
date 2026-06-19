# BUILD CARD - spinor_network_surface_v3 (the pre-registered statistic; the v2 no-rise fix)

You are codex2 (high). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build in `system_v6/sims/spinor_network_surface_v3/` (file-disjoint). NO git add/commit. Boundary helper FULLY: no builder-authored `audit_verdict.md`; envelope and packet validator must gate `no_builder_audit_verdict`.

## Authority

- Surface doctrine with all entries through `c710489ae`: v3 rule is binding. The statistic itself must be pre-registered before any run: predicted chart cells per structured family plus precommitted seeds.
- v2 mechanical repairs from `02d7d9fc6` are kept: rebuilt wrong-row control, in-packet Haar null, Kraus/Choi witness ledger, A33 kinematic ceiling, v1 floor anchors, all-three-engine recomputation, honest scratch ceiling.
- v1 floor remains the floor. v3 may report a positive, partial, or negative statistic; it must not promote the claim beyond what the computed comparison earns.

## Pre-Registration Frozen Before Computation

Classifier: committed A33 row set with cell ids generated as `A33_x{token}_y{token}_z{token}` over grid `[-1.0, -0.5, 0.0, 0.5, 1.0]` inside the Bloch ball.

Structured family predictions:

- `estate_chiral_quaternion_Hopf_Weyl`: predicted cells are the two +/-z-axis-adjacent rows in the family's committed +x/y0 meridian alignment:
  - `A33_xp5_y00_zm5`
  - `A33_xp5_y00_zp5`
- `entangled_nonproduct`: predicted cells are the z-row pair:
  - `A33_x00_y00_zm10`
  - `A33_x00_y00_zp10`

Seed ledger:

- v1 committed seed reused: integer `20260611`; hash `b625c2b83246f7e1f7093fb5157ee56cc6673a3a5640f5300bb0d40a10cabea8` for `{"dim":16,"source":"spinor_network_surface_v1","v1_committed_seed":20260611}`.
- New precommitted seeds:
  - integer `20260612`; hash `0a91af394146a18e03c1f7c9737a10e470c917a0c70a6d39a1e4b46da16506db`
  - integer `777`; hash `3c014267832b787e31201508352ca101bdbacbb4d2d2cf3a6cc56c0baaeafcbb`
  - integer `31337`; hash `4a017e0b7657f32d0843714c972db94a8b9b2ff6f088271214da6ad41657e3b1`

Pre-registered statistic:

- Compute the structured families' recovered A33 cells.
- Compare recovered predicted cells against the Haar null's identity distribution for the same fixed predicted cell set.
- Report the real result either way: all predicted cells recovered, partial recovery, no recovery, above null, or not above null.
- Do not substitute observed recovered cells for the pre-registered predicted cells. Observed-only cell sets may be diagnostic rows only.

Spurious extension:

- Keep v1/v2 equal pair-mixture spurious rows.
- Add the Hopfield-note three-pattern-mixture extension over the v1 anchor patterns `{chiral_quaternion_L, chiral_quaternion_R, entangled_nonproduct, pinned_random}`.
- Denominator is `C(4,3)=4`; enumerate all four equal three-pattern mixtures and persist terminal ids, coverage, and count.

## Required Carry-Forward From v2

1. Wrong-row control remains structure-sensitive and fails through the real predicate, not a string mismatch.
2. Haar null is computed in-packet.
3. Kraus/Choi witness ledger persists computed completeness, Choi positivity, trace, and partial-trace rows.
4. A33 reachability ceiling remains computed as 33.
5. V1 anchor cells reproduce where unchanged.
6. Three engines independently emit lanes; the envelope uses the standard helper and strict source-backed validator.
7. Classification remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Done Condition

The packet is done only when v3 result files are regenerated from v3 sources, the packet validator passes in builder phase, the generic three-engine validator passes with `--require-pytorch --strict-source-backed --require-tool-intent`, pytest passes, and the final envelope contains the pre-registration table, the actual fixed-statistic comparison, and the 3-pattern-mixture spurious table.
