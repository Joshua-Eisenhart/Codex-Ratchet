# Fresh Audit Verdict - terrain_spinor_flux_nest_n4_v0

Date: 2026-06-11
Auditor: codex2 cross-backend auditor
Scope: read-only audit of builder packet, except this verdict file
Comparator: committed `terrain_spinor_flux_nest_n3_v0` at `1b36e4a3c`
Audit bar: `system_v6/receipts/audit_bar_calibration_20260610.md`

## Bottom Line

Verdict: `GENUINE-WITH-CAVEATS`.

The n=4 packet is a real scratch-diagnostic integration artifact: it consumes the committed n4 stage carrier, derives a C^16 state vector from four parent site spinors, runs the terrain edge-current network on the 5-edge/2-face support, carries the n=3 G1/G2 hardening pattern forward, closes the n3 density-quotient weakness here, and has like-for-like Julia/JAX/PyTorch agreement on `conditioned_total_abs_current`.

The saturation decision is mixed. The three changed rows are computed and real, but only one is a substantive closure of a prior weakness (`density_quotient_control`); the other two are support-size/comparison-target bookkeeping. The behavior rows did not change class. This supports a bounded n=5 scout only if the owner wants to test whether the support-topology bookkeeping itself keeps changing; it does not justify n=5 as a new behavior-class continuation. On behavior-class evidence, the saturation signal is already firing.

Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; no bridge, axis, manifold, physics, formal-admission, promotion, actual n=5, or n>4 rung-evidence claim is supported.

## Commands And Fresh Checks

- Read source/results for n4 and committed n3 comparator.
- Recomputed carrier state vector/probability hashes from parent n4 site spinors with `PYTHONDONTWRITEBYTECODE=1` and no packet writes.
- Recomputed one continuity target site balance from stored scaled edge-current rows.
- Recomputed full density-quotient reproduction hash comparison against the committed n4 stage parent row.
- Recomputed first terrain edge coupling and current from the S5 z-row formula.
- Ran strict generic validator: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json` -> `{"ok": true}`.
- Ran load-bearing capability checks for JAX, PyTorch, and Julia source files -> all `violations: []`.

I did not rerun packet-local builders or `validate_terrain_spinor_flux_nest_n4_v0.py`, because those commands overwrite result JSONs and the user allowed writes only to this verdict file. I inspected the existing packet-local validator result: `ok=true`, `errors=[]`, `phase=builder`.

## Q1 - n=4 Carrier

Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:171-216` constructs `state` by ordered tensor product of each committed site's `psi_L`/`psi_R`, records `parent_state_vector_row_copied: False`, and emits `reconstructed_state_vector_sha256`. `terrain_spinor_flux_nest_n4_v0_common.py:987-1011` consumes `stage_jax["rows"]["P2_support_object"]["sites"]`, `edges`, and `faces`.

Recompute:

- stage sites/edges/faces: `4 / 5 / 2`
- envelope carrier dimension/site count/support edges/support faces: `16 / 4 / 5 / 2`
- local factor norms: q0=`1.0`, q1=`1.0`, q2=`1.0`, q3=`1.0`
- recomputed state norm: `0.999999999999` (rounding at 12 decimals; within bar)
- recomputed state hash: `00f7a6cd956d09d9372ffc356da4d0c3ec76bb13f641596e3108c5a1f8526b76`
- envelope state hash: `00f7a6cd956d09d9372ffc356da4d0c3ec76bb13f641596e3108c5a1f8526b76`
- recomputed probability hash: `e18acaf3d5116e2820084b8f6be1bf99aaecbc7bbde9b7b06dfa8563698ef2d0`
- envelope probability hash: `e18acaf3d5116e2820084b8f6be1bf99aaecbc7bbde9b7b06dfa8563698ef2d0`
- parent site rows hash: `a4db762169eaa01f17a11c5ad5a76ea24b6f8e4b7faaab3d2eb1324243565eff`

Adjudication: passes. This is a real C^16 carrier derived from committed n4 site spinors, not a support graph alone and not a copied parent state-vector row.

## Q2 - Closure Inheritance

### Continuity

Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:363-421` builds scaled edge-current formula rows, derives per-site edge divergence from outgoing minus incoming edge currents, and stores a target balance row. `terrain_spinor_flux_nest_n4_v0_jax.py:139-170`, `:186-227`, and `terrain_spinor_flux_nest_n4_v0_julia.jl:267-306` bind current/coupling/population/residual variables in solver space, derive divergence from edge-current variables, and assert the negated balance.

Recomputed target site `q1` from stored proof row:

- outgoing: `e12`; incoming: `e01`
- derived divergence scaled: `82698566379`
- row divergence scaled: `82698566379`
- local scaled: `13788250610`
- network scaled: `-68910315769`
- local minus derived: `-68910315769`
- balance residual recomputed: `0`
- z3: `unsat`, erased: `sat`
- cvc5: `unsat`, erased: `sat`
- Julia-Z3: `unsat`, erased: `sat`

Adjudication: the n3 G1 closure is inherited for the target proof row. Named caveat A1: this is not an all-site exact scaled proof. The stored site rows have scaled residuals `{q0: 1, q1: 0, q2: 0, q3: -1}` and derived-divergence exact matches `{q0: false, q1: true, q2: true, q3: false}`. The packet's float continuity row is still zero within declared precision, but the exact solver proof should be read as target-row continuity plus tolerance-level network continuity, not all-site integer exactness.

### Honest Control Language

Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:612-620` says the decoupling control checks same-schema `site_id/z_dot` rows and explicitly sets `byte_consistent_on_parent_exact_rows: False` because full row schemas differ.

Adjudication: passes. This replicates the committed n3 addendum closure: no overbroad full-row byte-stability claim is made.

### State-Vector Provenance

Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:203-218` records `carrier_source_kind: reconstructed_from_committed_stage_site_spinors`, `parent_state_vector_row_copied: False`, `parent_state_vector_provenance_rederived: True`, and both reconstruction hashes.

Adjudication: passes. The recompute above matches the emitted hash from parent site spinors. This is a real derivation, not a copied row with a new label.

### Density-Quotient Reproduction

Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:490-541` rederives the n4 density-quotient row and compares full stable SHA plus per-field hashes against `stage_lifted_spinor_shell_n4_v0_jax#rows.P3_density_quotient`.

Recomputed comparison:

- parent SHA: `2fc023eef930549da187be511ae42ddb582e2ee5f9f492b03b61043bd70d37fd`
- rederived SHA: `2fc023eef930549da187be511ae42ddb582e2ee5f9f492b03b61043bd70d37fd`
- full match: `true`
- matching fields: `density_only_collapse_control`, `erasure_table`, `ic_povm_separation`, `pass`, `phase_erasure_norm`, `reductions`, `rho` all `true`
- IC frame: d=`16`, effect_count=`256`, min_effect_eigenvalue=`0.0037109375`

Adjudication: passes. This closes the n3 density-quotient caveat here.

## Q3 - Saturation Table

The packet reports changed classes:

1. `carrier_support`
   - n3 class/value: `C^8_three_site_triangle_support`, `{dimension: 8, site_count: 3, edge_count: 3}`
   - n4 class/value: `C^16_four_site_two_face_support_complex`, `{dimension: 16, site_count: 4, edge_count: 5, face_count: 2}`
   - Adjudication: real computed class change. It is support-topology/carrier-size class, not a new terrain behavior class by itself.

2. `decoupling_control`
   - n3 class/value: `same_schema_z_dot_against_terrain_parent_3_site`, target `terrain_spinor_shell_nest_v0`, max error `0.0`
   - n4 class/value: `same_schema_z_dot_against_stage_n4_s5_s6_rows_4_site`, target `stage_lifted_spinor_shell_n4_v0.P8_shell_leakage.s5_s6_generator_lineage`, max error `0.0`
   - Adjudication: real table class change, but it is comparison-target bookkeeping caused by the fourth site living in the n4 stage packet. It does not show a new decoupling behavior.

3. `density_quotient_control`
   - n3 class/value: `hash_count_recovery_weak_control`, `full_reproduction: false`
   - n4 class/value: `full_rederived_density_quotient_reproduction`, `full_reproduction: true`
   - Adjudication: real and substantive as an audit/provenance closure. It is not a new terrain dynamics behavior; it closes a prior weakness.

Unchanged/rescale rows:

- `terrain_edge_couplings`: same `pairwise_S5_z_row_edge_coupling`; edge count changes `3 -> 5`.
- `flux_continuity`: same `in_solver_edge_current_continuity`; edge count changes `3 -> 5`; z3/cvc5 remain `unsat`.
- `k_leaf_conditioning`: same `finite_k_leaf_conditioning`; leaf count changes `3 -> 4`; weight sum remains `1.0`.
- `network_observable_signatures`: same `narrowing_alteration_path_specificity`; n3 bare/conditioned total abs current `0.735575785391 -> 0.242675773674`, n4 `1.100562920308 -> 0.260547429214`; magnitude changes only.
- `terrain_drop_control`: same `zero_terrain_recomputed_bare_network`; edge count changes `3 -> 5`; committed bare-current parent row remains un-compared.

Decision: mixed, leaning saturation for behavior. The table does not justify a broad n=5 continuation on behavior-class grounds. It justifies, at most, a narrow bounded n=5 scout to test whether support-topology bookkeeping keeps changing or stabilizes. If the owner's stop criterion is "new behavior class," n=5 is not justified and saturation is already firing. If the stop criterion includes "new support complex class," a single narrow n=5 scout is justified, but only with the ceiling and bookkeeping label explicit.

## Q4 - Standard Checks

Terrain edge couplings:

- Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:295-301` defines `g_ij=abs((zdot_i+zdot_j)/2)+0.25*(abs(A_zx)+abs(A_zy)+abs(A_zz))+abs(b_z)`.
- First edge recompute for `e01`: A_zx=`-2*sqrt(3)/15`, A_zy=`2*sqrt(3)/15`, A_zz=`-4/5`, b_z=`0`, q0 z_dot=`-0.782956784955`, q1 z_dot=`-0.027576501221`, coupling=`0.720736696926`, population_delta=`-0.25`, current=`-0.180184174231`.
- Recorded values match exactly at 12 decimals.

k-leaf conditioning:

- Source quote: `terrain_spinor_flux_nest_n4_v0_common.py:280-292` computes `w_i=sin(2*eta_i)/sum_j sin(2*eta_j)`, and `:323-324` applies `sqrt(w_i*w_j)` to conditioned edge strengths.
- PyTorch source quote: `terrain_spinor_flux_nest_n4_v0_pytorch.py:104-115` symbolically checks the k-leaf weight sum defect is `0`.

Collapse controls:

- `decoupling_edges_recovers_rung2_per_site`: passes with honest same-schema `z_dot` comparison only.
- `density_quotient_recovers_committed_n4_ladder`: passes with full row hash match.
- `dropping_terrain_recovers_bare_network`: passes zero-coupling/current/flux recompute, but carries the same G3 structural remainder: no committed bare-current parent row comparison.
- `permuted_etas`, `shuffled_couplings`, and `naive_conditioning_fails`: pass and are real can-fail controls.

Schema and ceiling:

- `schema_version: three_engine_sim_result_v1`
- `classification: scratch_diagnostic`
- `ceiling: scratch_diagnostic`
- `mode: RATCHETED`
- `standard_schema_mode: FIELD`
- `engine_contract.mode: RATCHETED`
- `engine_contract.mode_is_field: true`
- `promotion_allowed: false`
- `formal_admission_allowed: false`
- seed: `2026061104`

Engine agreement:

- metric: `conditioned_total_abs_current`
- Julia: `0.260547429214`
- JAX: `0.260547429214`
- PyTorch: `0.260547429214`
- max divergence: `0.0`, tolerance `1e-8`
- pin identical across legs: `true`

Real Julia leg:

- Source uses `QuantumOptics`, `ITensors`, `ITensorMPS`, and `Z3` at `terrain_spinor_flux_nest_n4_v0_julia.jl:7-15`.
- Julia receipt reports package versions: `QuantumOptics 1.2.6`, `ITensors 0.9.30`, `ITensorMPS 0.4.1`, `Z3 1.0.4`.
- Source quote: `terrain_spinor_flux_nest_n4_v0_julia.jl:212-226` builds a `QuantumOptics.NLevelBasis/Ket/tensor/dm` density receipt; `:229-241` builds an ITensor/MPS receipt; `:267-306` runs the Julia-Z3 proof.

Proof tools and erased flips:

- z3: `unsat`, erased flip `sat`
- cvc5: `unsat`, erased flip `sat`
- Julia-Z3: `unsat`, erased flip `sat`

Parent lineage and capabilities:

- parent lineage is hash-bound and includes the required seven parents: `stage_lifted_spinor_shell_n4_v0`, `terrain_spinor_shell_nest_v0`, `geo_s5_terrain_flows_v0`, `ratchet_s2_two_shell_flux_v0`, `geo_disintegration_machinery_v0`, `geo_union_rule_k_leaves_v0`, `terrain_exact_mirror_finder_v0`.
- one-to-one capability/tool-call IDs match exactly: `carrier_stage_n4_network`, `terrain_z_row_coupling`, `flux_continuity_z3`, `flux_continuity_cvc5`, `julia_network_quantum_leg`, `ratcheted_k_leaf`.
- strict source-backed generic validator passes.
- load-bearing capability checks pass for JAX, PyTorch, and Julia with no violations.

Wording and claim boundary:

- Packet source disallows `actual n=5 run or n>4 rung evidence`.
- Build card and hardening addendum explicitly say no actual n=5 result, no universal mirror law, no bridge/axis/physics/manifold claim, no promotion, and no formal admission.
- No forbidden fixture wording was found in source/metadata scan excluding this audit file.

## Named Caveats

- A1 - Target-row exactness caveat: solver continuity is genuine for the selected target row `q1` and supported by float/tolerance continuity across the packet, but q0/q3 have stored scaled residuals `+1/-1`. Do not call the solver proof an all-site exact scaled proof.
- A2 - G3 still carried: zero-terrain recompute is real, but there is still no committed bare-current parent row comparison.
- A3 - Saturation interpretation caveat: the emitted `n5_value_signal` treats any class change as value for a bounded n5 scout. Under the owner's behavior-vs-bookkeeping question, two of the three class changes are bookkeeping/target changes and one is an audit-closure change.

## Final Verdict

`GENUINE-WITH-CAVEATS`.

The n4 artifact passes the calibrated bar as a scratch diagnostic. The carrier, terrain edge couplings, target in-solver continuity, density-quotient reproduction, k-leaf conditioning, collapse controls, parent lineage, source-backed tool claims, and cross-backend agreement are real.

n=5 recommendation: `MIXED`. Justified only as a narrow, bounded support-topology/bookkeeping scout; not justified as a behavior-class continuation. If the owner is deciding whether the terrain mechanism has saturated, the computed table supports "saturation likely firing" because the behavior rows keep the same class while only carrier/support bookkeeping, comparison target, and density-quotient proof strength change.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; no n>4 claim, no actual n=5 result, no bridge/axis/manifold/physics claim.
