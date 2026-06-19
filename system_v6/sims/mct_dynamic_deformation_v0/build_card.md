# BUILD CARD: mct_dynamic_deformation_v0 - dynamic deformation geometry of M(C,t)

One object, one claim, one card. Claim under test: using the committed
`mct_dynamic_admissibility_packet_v0` finite support and the committed
RATCHETED packets as the `t` direction, compute how the admissible set
`M(C,t)` deforms, and compute which deformation patterns are excluded.

Ceiling: `classification="scratch_diagnostic"`,
`promotion_allowed=false`, `formal_admission_allowed=false`. This packet is
deformation geometry of the admissible set only. It makes no bridge, axis,
physics, manifold-admission, or formal-admission claim.

## Binding Inputs

1. Parent M(C,t) packet:
   `system_v6/sims/mct_dynamic_admissibility_packet_v0/` and especially
   `results/mct_dynamic_admissibility_packet_v0_*_results.json`.
2. Canonical program receipt:
   `system_v6/receipts/geometry_sim_program_canonical_20260610.md`, S11:
   `M(C,t)={x in A_t : C_i(x) holds}/~_P`, with time maps and five operations.
3. Reconciled M(C,t) tuple:
   `system_v6/receipts/mct_reconciled_spec_20260609.md`, fields
   `S_t, C_t, Probe_t, Val_t, ~_t, Q_t, Adm_t, E_t, Poss_t, H_t, R_t, Var_t,
   U_t, Ctrl_t, Rec_t`.
4. Committed RATCHETED `t` paths:
   `ratchet_s1_single_shell_pilot_v0`,
   `ratchet_s2_two_shell_flux_v0`,
   `ratchet_s2_three_shell_chain_v0`,
   `ratchet_s6_terrain_operator_shell_v0`,
   `ratchet_s6_terrain_sweep_v0`,
   and `geo_union_rule_k_leaves_v0`.
5. Compression/radiated-record coordination:
   `compression_flow_radiated_record_v0` and
   `system_v6/receipts/shell_flow_radiated_information_mine_20260610.md`,
   cited as framing/ledger convention only.

## Computation Scope

- THE OBJECT: a finite `M_t` ledger over the parent 384-row support table.
- DEFORMATION MODES:
  - `COMPRESSION`: admissible-measure decrease under pure constraint addition,
    plus parent quotient compression by probe coarsening.
  - `WARP`: relation/shape change at constant support/admissible measure, with
    graph-shape invariants before and after.
  - `EXPANSION`: admissible-measure increase only under constraint release or
    probe refinement, with the finite k-leaf full-measure limit cited as anchor.
- RIGIDITY / EXCLUSION ROWS:
  - Pure constraint addition cannot expand: proved over computed finite
    membership rows with z3 and cvc5; erased/release control flips to SAT.
  - Quotient readout erasure is irreversible inside the quotient: proved by a
    same-class/different-phase pair; phase-refined control flips.
  - Topological/convention anchors remain pinned in these finite deformations:
    `c1_abs=1`, chain additivity defect `0`, and cover factor `2`.
  - Open rows explicitly list what the finite evidence cannot decide.
- COMPRESS/RADIATE LINK:
  - For compression rows, record excluded counts and named entropy deltas.
  - The radiated-record language is framing only here; it is not promoted.

## Required Files

`system_v6/sims/mct_dynamic_deformation_v0/`

- `mct_dynamic_deformation_v0_jax.py`
- `mct_dynamic_deformation_v0_julia.jl`
- `mct_dynamic_deformation_v0_envelope.py`
- `validate_mct_dynamic_deformation_v0.py`
- `build_card.md`
- `results/*.json`

Do not create `audit_verdict.md`. Do not edit parent packets. Do not git add or
commit.
