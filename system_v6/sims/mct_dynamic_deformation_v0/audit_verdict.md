# Audit verdict: mct_dynamic_deformation_v0

Verdict: GENUINE-WITH-CAVEATS.

Calibrated bar used: `system_v6/receipts/audit_bar_calibration_20260610.md`.
Scope: read-only audit of builder artifacts, with this `audit_verdict.md` as the only write.

## Source Pins

- Object and ceiling: the build card says the packet uses the committed `mct_dynamic_admissibility_packet_v0` finite support and committed RATCHETED packets as the `t` direction to compute how `M(C,t)` deforms and which patterns are excluded (`build_card.md:3-6`). It also says the ceiling is `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, and that the packet makes no bridge, axis, physics, manifold-admission, or formal-admission claim (`build_card.md:8-11`).
- Program object: S11 defines `M(C,t)={x in A_t : C_i(x)} / ~_P` with time maps and five operations (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:27`).
- Pre-registration: panel 6 q5/q6 pre-registers pure-addition monotonicity and quotient/projection irreversibility as the dynamic-manifold lane's lead rigidity rows (`system_v6/receipts/cross_model_anchor_recompute_panel6_20260611.md:11-16`). Commit `e2ca51b02` contains that receipt.

## Q1 Object

Pass. The finite representation is pinned to the parent support table:

- Envelope `M_C_t_object.definition`: `M(C,t)=the admissible set under active finite constraint family C(t), quotient by active probe equivalence ~_P; t is the committed ratchet sequence parameter`.
- Envelope finite representation: parent probe table source `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_jax_results.json`, support size `384`, `q_without_phase=24`, `q_with_phase=192`, support hash `5727f366d2e4081549095d62741e25179aa6e561042617ba70970173b74bc2a8`.
- Source refs name the ratchet path receipts for `ratchet_s1_single_shell_pilot_v0`, `ratchet_s2_two_shell_flux_v0`, `ratchet_s2_three_shell_chain_v0`, `ratchet_s6_terrain_operator_shell_v0`, `ratchet_s6_terrain_sweep_v0`, and `geo_union_rule_k_leaves_v0`.

## Q2 Mode Ledger

Pass. Non-writing JAX recomputation of `build_result()` returned:

- Compression row 1: `384 -> 256`, excluded `128`, `H_Q` delta `-0.40546510810816416`, operation `ADD_F01`.
- Compression row 2: `256 -> 206`, excluded `50`, `H_Q` delta `-0.08396883945513745`, operation `ADD_N01`.
- Warp row: admissible count `206 -> 206`, support `384 -> 384`, relation edges `1664 -> 1600`.
- Warp edge delta recomputed from source functions: `shell_nested` edges `512 -> 384`, `warp_long_shell_jump` added `64`, net edge count `-64`.
- Shape invariant moved: JAX bottom Laplacian row changes at the sixth value, `1.0 -> 1.171572875`, and spectrum hash changes `fc3c1... -> 322301...`.

The warp is therefore a genuine constant-measure shape change, not a hidden compression or expansion. Julia independently recomputed `adm_active=206`, edge counts `1664 -> 1600`, and the same bottom-eigenvalue movement.

## Q3 Rigidity Rows

### Q3a Monotonicity

Pass. The encodings derive inclusion from computed finite sets, not an asserted boolean:

- JAX computes row sets from parent rows and predicates `F01`/`N01` (`mct_dynamic_deformation_v0_jax.py:125-143`), builds `old_active`, `new_active`, and release controls from those sets (`mct_dynamic_deformation_v0_jax.py:447-455`), then binds every row to SMT integer variables and asks whether any `new_i > old_i` exists (`mct_dynamic_deformation_v0_jax.py:225-241`, `264-281`).
- Julia mirrors the same row-set construction (`mct_dynamic_deformation_v0_julia.jl:95-108`), old/new/release vectors (`mct_dynamic_deformation_v0_julia.jl:240-252`), and Z3 row binding (`mct_dynamic_deformation_v0_julia.jl:177-204`).

Recomputed verdicts:

- JAX z3 pure-addition expansion: `unsat`; release control: `sat`.
- JAX cvc5 pure-addition expansion: `unsat`; release control: `sat`.
- Julia Z3 pure-addition expansion: `unsat`; release control: `sat`.
- F01 addition check also returns z3 `unsat` with release control `sat`.

The expansion rows are release rows, not pure-addition rows: `RELEASE_N01` gives `206 -> 256`, and `RELEASE_F01_AND_N01` gives `206 -> 384`.

### Q3b Quotient Irreversibility

Pass with finite-scope wording. JAX selects a same-quotient/different-phase pair from the parent row table (`mct_dynamic_deformation_v0_jax.py:295-304`) and then forces a single recovered quotient-class phase to equal two different phase values (`mct_dynamic_deformation_v0_jax.py:307-347`).

Recomputed pair and verdict:

- Pair: `L:eta0:phi0:chi0` and `L:eta0:phi0:chi4`.
- Same no-phase quotient key: true.
- Different phase values: `[0, 4]`.
- z3 recovery from no-phase quotient: `unsat`; phase-refined control: `sat`.
- cvc5 recovery from no-phase quotient: `unsat`; phase-refined control: `sat`.

Honest meaning: no admissible operation in this packet's available no-phase quotient readout can recover the erased `P_phase` distinction for the demonstrated same-class pair. It does not prove arbitrary downstream recovery is impossible outside the scoped operation/readout family.

### Q3c Pinned Invariants

Pass. Recomputed JAX and Julia values agree:

- `c1_abs = 1`.
- `chain_additivity_defect = 0`.
- `cover_factor = 2`.
- `changed_by_available_deformations = false`.

These invariants did not move across the committed finite deformation ledger. The should-change warp invariant did move, so the invariant machinery is not trivially frozen.

### Q3d Open Rows

Pass. The envelope carries honest open rows:

- finite rows do not decide arbitrary smooth deformations of a continuum manifold;
- finite rows do not decide topology-changing operations outside the committed support/quotient family;
- release controls show expansion is possible but do not classify every future release path;
- radiated-record framing is convention/framing only, not physics or conservation doctrine.

## Q4 Controls

Pass.

- Release expands: fired, `active_count=206`, `released_N01_count=256`; release-all row reaches `384`.
- Pure addition never expands: z3/cvc5/Julia Z3 all `unsat`.
- Should-change-under-warp invariant changes: edge count and spectrum/eigenvalue rows move.
- Controls can fail: release controls are SAT, phase-refined quotient control is SAT, and the warp identity control would preserve the spectrum hash.

## Q5 Standard

Pass with scoped two-lane mode.

- Schema: `three_engine_sim_result_v1`.
- Mode/lanes: `julia_canon_plus_jax_smt_deformation_diagnostic`, lanes `["julia", "jax"]`; PyTorch is explicitly omitted because there is no graph/network/autograd claim path beyond Julia `Graphs`.
- Parent lineage: envelope lists parent MCT, geometry program, reconciled spec, ratchet paths, k-leaf anchor, and compression-flow framing hashes.
- Julia leg: real Julia leg exists and recomputes counts, graph shape, pinned invariants, and Julia Z3 monotonicity.
- Capability receipts: present for JAX z3/cvc5/sympy and Julia Graphs/Z3, with versions.
- Tool calls: six one-to-one load-bearing tool calls match `claim_path_tools`: `jax`, `sympy`, `z3`, `cvc5`, `Graphs`, `Z3`.
- Seeds: deterministic/no RNG, SMT seed ledger present.
- Validator: `scripts/validate_three_engine_sim_result.py ... --require-source-backed --strict-source-backed` returned `ok:true`.
- Fixture wording: no `fixture`, `toy`, `stub`, or `mock` wording appears in the target packet files.
- Fences: target files keep `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; `build_card.md:8-11` explicitly excludes bridge, axis, physics, manifold-admission, and formal-admission claims.

## Q6 Closure

Earned:

- A finite `M(C,t)` deformation ledger over the parent 384-row table.
- Computed compression rows with real admissible-measure decreases.
- A genuine WARP row: constant admissible count `206`, constant support `384`, relation shape changed `1664 -> 1600`, spectrum/eigenvalue witness changed.
- Two pre-registered finite-scope rigidity results: pure-addition monotonicity and quotient-readout irreversibility.
- Pinned invariants under the available finite deformations: `c1_abs=1`, chain additivity defect `0`, cover factor `2`.

Not earned:

- No continuum deformation theorem.
- No full manifold-level admission.
- No bridge, axis, or physics claim.
- No claim that every future release/refinement path is classified.
- The owner's `warp/compress/expand` vocabulary is admitted as interpretation over computed finite modes, not as a new canonical geometric doctrine.

## Named Caveats

- G1 finite-scope rigidity: monotonicity and quotient irreversibility are proven over the computed finite row universe and available quotient/readout operations. They should not be restated as arbitrary continuum or all-possible-operation theorems.
- G2 hash representation nuance: JAX and Julia agree on counts, edge counts, eigenvalue movement, and post-warp hash; the pre-warp spectrum hash differs because one backend serializes the rounded zero row as `-0.0` and the other as `0.0`. This does not affect the measured warp but should not be used as a byte-stability claim.

Final ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
