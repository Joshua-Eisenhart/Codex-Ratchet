# Audit verdict - geo_s6_stacked_flows_hopf_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/geo_s6_stacked_flows_hopf_v0/`, except this `audit_verdict.md`.

Verdict: **REJECT AS CLAIMED; ACCEPT AS USEFUL SCRATCH ARITHMETIC PACKET**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as canonical stacked geometry, Axis admission, runtime closure, physics, completed constraint manifold, or formal admission.

## Inputs Read

- Sim folder: `system_v6/sims/geo_s6_stacked_flows_hopf_v0/`
- Blind expected: `/tmp/s6_blind_expected_20260610.md`
- Build spec: `system_v6/receipts/s6_build_spec_20260610.md`
- Nesting law: `system_v6/receipts/nesting_law_audited_20260610.md`
- Pattern catalog H1-H7: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md:81-205`
- Pattern catalog E1-E6: `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md:332-415`
- S4-v2 six: `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:326-400`
- S5-v2 six: `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:326-446`

The local packet validator and generic three-engine validator both pass:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s6_stacked_flows_hopf_v0/geo_s6_stacked_flows_hopf_v0_exact_strength_validator.py
ok: true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json
ok: true
```

Those are shape/source-backed validator passes, not the stronger audit result.

## K1 - dz/dt, Classification, Leakage Integrals

Status: **PASS for generator-derived `dz/dt` and integral arithmetic; GAP for sensitivity strength.**

Source lineage exists. The JAX leg imports S5 `A,b` rows and does not rebuild a second S5 table: `exported_rows()` reads `s5["bloch_generator_table"]`, parses `row["pinned"]["A"]` and `row["pinned"]["b"]`, and records `source_ref` (`geo_s6_stacked_flows_hopf_v0_jax.py:294-307`). The leakage path then computes `vector_field = A * r + b`, `z_dot = vector_field[2,0]`, and `purity_derivative = 2 * r.dot(vector_field)` (`geo_s6_stacked_flows_hopf_v0_jax.py:363-377`). This matches the build spec requirement that `z_dot=e_z^T(A r_eta+b)` be derived from exported S5 rows (`system_v6/receipts/s6_build_spec_20260610.md:60-80`).

Hand recomputation:

```text
Ne_Vortex_L exported A,b -> dz/dt
= -2*sqrt(6)*sin(2*eta)*cos(2*chi + pi/4)/3
recorded formula matches exactly.
```

The blind sign trap is handled: blind expects left Ne as `2(y-x)/sqrt(3)` and right Ne as `2(x-y)/sqrt(3)` (`/tmp/s6_blind_expected_20260610.md:27-35`). The current left-row formula is equivalent to the left sign.

Classification mostly matches blind expectations. The packet records `Ne/* -> cross_shell`, `Se/* -> leave_foliation`, `Ni/* -> leave_foliation`, `Si/Hill -> projected_shell_preserve_but_Hopf_leave`, and `Si/Citadel -> leave_foliation` in `terrain_summary`; this matches the blind classification table except that `Si/Citadel` is correctly nonunitary because the exported row has active dephasing (`/tmp/s6_blind_expected_20260610.md:155-166`).

Leakage integral recomputation:

```text
Si_Citadel_R z_dot = 2*sin(2*chi)*sin(2*eta)/5 - 2*cos(2*eta)/5
eta = pi/4, chi0 = pi/8, P = 2*pi lifted chart cycle
L_inner = 2*sqrt(2)*pi/5
L_outer = 0
recorded placement 15 pi/4 values match exactly.
```

The packet distinguishes shell leakage from sphere/purity leakage. It records `purity_derivative_formula` separately from `z_dot_formula` for every row, and blind explicitly says `dz/dt` is not radial leakage (`/tmp/s6_blind_expected_20260610.md:61-72`).

Named gap K1.1: `chi0=pi/8` is an accidental zero for the `H0=(x+y+z)/sqrt(3)` precession term. As a result, many phase-dependent rows have `L_inner == L_outer` even though blind expects inner/outer distinction on phase-dependent rows except accidental points (`/tmp/s6_blind_expected_20260610.md:118-131`, `168-197`). The formulas are correct and phase-dependence is still recorded, but the chosen basepoint weakens the loop-swap evidence.

Double-cover status: the packet names the lifted chart convention: `loop_period=2*pi_lifted_chart_cycle`, and the convention pin says `chi:0->2*pi traverses base twice`. That handles the tripwire as a declared lifted-chart integral, but it does not emit a paired one-density-loop `P=pi` value. This is acceptable for a declared lifted-cycle scratch result, not for any physical-period overclaim.

## K2 - A/F/h/Phi_ij Terrain Action

Status: **FAIL for the requested transported-loop standard.**

Arrow types are named, and the nesting law requires that every sim name its arrow type (`system_v6/receipts/nesting_law_audited_20260610.md:15-29`). S6 also requires every map to declare RESTRICTED/STACKED mode and name arrow type (`system_v6/receipts/s6_build_spec_20260610.md:152-157`). The packet satisfies that surface.

The stronger K2 requirement is not met. For pure Ne rows, `terrain_action_rows()` samples one spinor point and two tangent kinds, computes a local connection delta, and reports `Phi_T_star_A_minus_A = 0` from that sample (`geo_s6_stacked_flows_hopf_v0_jax.py:449-475`). This is not transport along the flowed inner/outer loops, and it does not compute a loop-level `h(Phi_T(T_eta))-h(T_eta)` or a shell-transition map from transported loop images.

The result itself says no coherent shell map exists for pure Ne rows: `Phi_ij = undefined_no_coherent_shell_map`, with `h_action = no single h(...) scalar`. That part agrees with blind expectations for pure rotations about `(1,1,1)` (`/tmp/s6_blind_expected_20260610.md:143-153`). But calling the row a computed `A/F/h` action is too strong for the audit target because only a local tangent sample was checked.

For nonunitary rows, the packet correctly blocks pure-Hopf `A/F/h/Phi_ij` as `undefined_without_mixed_lift`, matching blind tripwire 8 (`/tmp/s6_blind_expected_20260610.md:223-238`).

Named gap K2.1: no transported-loop computation for `A/F/h/Phi_ij`; only local connection-delta sampling on pure Ne rows.

## K3 - Sixteen Placements

Status: **PASS for computed rows; GAP for loop-swap breadth.**

The build spec requires all 16 `(X_{a,s},Y_l)` rows to be computed pairings, not copied labels (`system_v6/receipts/s6_build_spec_20260610.md:92-103`, `158`). The packet builds placements from `PLACEMENT_ORDER`, attaches imported S5 row id/hash, z-dot formula, representative inner/outer/bar integrals, shell classifications, and `A_F_h_action_status` (`geo_s6_stacked_flows_hopf_v0_jax.py:492-544`).

Hand recomputation of one placement:

```text
placement_id = 15
terrain_row_id = Si_Citadel_R
loop_id = Y_inner
z_dot = 2*sin(2*chi)*sin(2*eta)/5 - 2*cos(2*eta)/5
eta = pi/4: inner = 2*sqrt(2)*pi/5, outer = 0
recorded placement values match exactly.
```

Named gap K3.1: because `chi0=pi/8` kills the H0 oscillatory term, the loop-swap control only visibly changes the `Si/Citadel` rows. Blind expects loop swap to change phase-dependent rows such as Ne and Hamiltonian parts of Se/Ni except at accidental points (`/tmp/s6_blind_expected_20260610.md:168-197`). This does not make the placement table label-only, but it weakens the placement control.

## K4 - g_DI, Shared Carrier, Axis-4 vs Axis-6

Status: **PASS at scratch ceiling.**

The packet defines one shared carrier before computing `Phi_D` and `Phi_I`: `density/Bloch carrier because E=Si_Hill_L is nonunitary dephasing` (`geo_s6_stacked_flows_hopf_v0_jax.py:589-658`). It computes:

```text
U = expm(A_Ne_Vortex_L)
E = expm(A_Si_Hill_L)
Phi_D = U @ E @ U @ E
Phi_I = E @ U @ E @ U
g_DI = ||rho(Phi_D(r)) - rho(Phi_I(r))||_1
```

Hand recomputation:

```text
commuting control with U=Ne_Vortex_L and E=Se_Funnel_L:
eta=pi/12, r=(sin(pi/6),0,cos(pi/6))
g_DI = 5.72e-17
recorded max_g = 5.24e-17

noncommuting sample with E=Si_Hill_L:
eta=pi/12, chi=0
g_DI = 0.35423441716684634
recorded sample = 0.35423441716684667
```

The blind expected `g_DI = ||D(I(rho)) - I(D(rho))||_1` on one shared carrier and commuting control near zero (`/tmp/s6_blind_expected_20260610.md:199-221`). The packet satisfies that.

Axis-4/Axis-6 separation is preserved. `loop_order_gap` is the S6 `Phi_D/Phi_I` metric. Matrix64 `Delta_T,O` is joined only in `matrix64_overlay_rows`, with `recomputed_matrix64=false` and relation labels such as `both_nonzero_independent_observables` (`geo_s6_stacked_flows_hopf_v0_jax.py:548-578`; envelope assembly at `geo_s6_stacked_flows_hopf_v0_envelope.py:237-246`). This avoids the H7 collapse pattern in `axis_independence_discriminators_036/audit_verdict.md:193-205`.

## K5 - Gates, Controls, Engines, SMT, Tools, Ceilings

Status: **FAIL in substance despite validator pass.**

What passes:

- Packet-local validator passes with no errors.
- `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` passes.
- Cross-engine exact signature fatality is wired in the envelope: row signatures and `loop_order_g_DI_scaled_1e9` must match Julia/JAX/PyTorch (`geo_s6_stacked_flows_hopf_v0_envelope.py:125-149`, `172-196`).
- SMT is honestly scoped as a measured finite scaled-gap contradiction, not a full symbolic proof (`geo_s6_stacked_flows_hopf_v0_jax.py:661-693`).
- PyTorch is bounded to a tensor/autograd mirror role with `torch.func`, z3, and cvc5 in claim-path tools; it is not the semantic arbiter.
- Ceilings are preserved in all legs and the envelope.

What fails the exactness bar:

1. `P10_round_trip_gates` is not a real round-trip gate. It passes when every shell row has a `z_dot_formula` and the loop-order gap is positive (`geo_s6_stacked_flows_hopf_v0_jax.py:920-922`). That does not differentiate the leakage formulas back to exported `A*r+b`, does not apply finite-time shell updates back to the generator, and does not meet the S6 build spec's round-trip wording (`system_v6/receipts/s6_build_spec_20260610.md:160-163`).

2. Several negative controls are evidence-surface records, not actual mutation reruns through the gates. The source constructs many rows with `executed=true`, `computed_mutation=true`, `gate_passed_after_mutation=false`, and fixed `mutated_observed` payloads (`geo_s6_stacked_flows_hopf_v0_jax.py:696-874`). Some controls compute useful numeric differences, such as wrong `H_R` and wrong Si frame, but many do not rerun the mutated packet path. This regresses toward the H4/S4-v1 failure mode, even though the validator enforces the booleans.

3. The exact-strength validator explicitly says it is a builder drift guard, not independent audit evidence (`geo_s6_stacked_flows_hopf_v0_exact_strength_validator.py:1-5`). It verifies fields and sentinel values (`geo_s6_stacked_flows_hopf_v0_exact_strength_validator.py:59-184`), but cannot close the stronger K2/K5 audit gaps above.

4. Julia is a carrier-signature mirror with `LinearAlgebra` and Z3, not a richer Julia Canon geometry lane. That is acceptable at this scratch ceiling because the packet imports S5 `A,b`, but it blocks any stronger three-engine/canon language.

## Pattern-Catalog Binding

H1-H7: no full fixture-isolation or label-echo collapse found in the main arithmetic path. The packet computes from imported `A,b` and shared carrier maps rather than only reading labels. However, K5 repeats the H4-style risk: controls can be made to pass by asserted mutation records rather than actual rerun evidence. See `axis_independence_discriminators_036/audit_verdict.md:140-160`.

E1-E6: sign pins and symbolic formulas are much better than the rejected exact-closure v1 pattern. The Ne sign recomputation passes, and the result does not rely on float-boxed tolerances for the checked formulas. See the E1/E2 closure standard in `geo_s1_exact_closure_v0/audit_verdict.md:332-358`.

S4-v2 six: S6 does not meet the S4-v2 executed-control standard. S4-v2 independently recomputed at least one mutation and showed concrete failing values (`geo_s4_operator_stage_v0/audit_verdict.md:342-355`). S6 mostly records would-fail mutation rows.

S5-v2 six: S6 consumes S5 exported `A,b` correctly, including the repaired Ne rows (`geo_s5_terrain_flows_v0/audit_verdict.md:326-360`). But S6 does not reproduce the S5-v2 round-trip strength: S5 differentiated flow formulas and compared residuals to exported `A*r+b` (`geo_s5_terrain_flows_v0/audit_verdict.md:361-377`), while S6 P10 is only a presence/positive-gap check.

## Final Verdict

**REJECT AS CLAIMED** against the requested exactness bar.

Accept as:

- source-backed scratch arithmetic for S6 `dz/dt` formulas from exported S5 `A,b`;
- computed leakage integral rows under the declared lifted-chart `2*pi` convention;
- computed 16 placement rows with imported S5 ids and shell classifications;
- computed `g_DI` on one density/Bloch carrier with a near-zero commuting control;
- source-backed, validator-green three-engine envelope at scratch ceiling.

Reject as:

- transported-loop computation of terrain action on `A/F/h/Phi_ij`;
- fully executed mutation-control proof;
- full S6 exact round-trip/consistency closure;
- canonical stacked geometry, Axis admission, runtime closure, physics, completed constraint manifold, or formal admission.

Required repair:

1. Replace the K2 pure-row local connection sample with transported-loop computations over the flowed `Y_in` and `Y_out` loops, reporting `A`, `F`, `h`, and `Phi_ij` from the transported loops or explicitly keeping them undefined.
2. Add a non-accidental `chi0` or a second basepoint so phase-dependent inner/outer placement controls change for Ne and Hamiltonian Se/Ni rows, not only `Si/Citadel`.
3. Rebuild `P10` as an actual round-trip: differentiate symbolic leakage/finite-time shell updates back to exported `A*r+b`, and rerun loop-order closed forms against their maps.
4. Make mutation controls execute mutated inputs through the same gates, not just record would-fail observations.
5. Preserve the current ceiling even after repair unless a separate formal admission gate is built and passed.

## V2 Re-Audit - 2026-06-10

Scope: fresh read-only re-audit of v2 after the prior `REJECT AS CLAIMED`; only this section was appended.

Verdict boundary: this re-audit checks the v1 fail conditions against v2. It does not promote the packet beyond `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Commands/checks rerun:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s6_stacked_flows_hopf_v0/geo_s6_stacked_flows_hopf_v0_exact_strength_validator.py
ok: true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json
ok: true

In-memory JAX `build_result()` rerun, without writing results:
fresh all_pass: true
fresh build_gates_false: []
fresh round_trip: true, finite_time_derivative_max_error=1.314588836351091e-10, loop_order_map_recompute_max_error=5.714040351989524e-13
fresh controls: all_executed_can_fail=true, control_count=18
```

### V1 - Transported-Loop `A/F/h/Phi_ij`

Status: **PASS at numerical transported-loop scratch ceiling.**

The v2 source no longer uses the v1 local tangent sample as the terrain-action evidence. `loop_spinor_points()`, `transported_surface_flux()`, and `transported_loop_diagnostic()` flow full `Y_inner`/`Y_outer` loops by `Phi_t`, re-integrate the Hopf connection on the flowed loop, and integrate curvature over the transported surface. Pure `Ne` rows report transported-loop integrals; nonunitary rows remain `undefined_without_mixed_lift`.

Independent recomputation of one transported holonomy:

```text
row: Ne_Vortex_L
eta: pi/6
loop: Y_outer
independent samples: 1440

A_unflowed = 3.1415826850174953
A_flowed = 3.1415826850174984
A_delta = 3.1086244689504383e-15
stored A_delta = 1.7763568394002505e-15
abs_delta = 1.3322676295501878e-15

z_spread = 1.7293420452040575
h_spread = 10.86577652951403
Phi_ij = undefined_no_coherent_shell_map
stored Phi_ij = undefined_no_coherent_shell_map
```

Independent recomputation of the same transported-surface `F` quadrature at the stored grid reproduced the result:

```text
F_transport_surface_integral = -3.3016287881088506
stored F_transport_surface_integral = -3.301628788108855
abs_delta = 4.440892098500626e-15
```

This closes the v1 K2 failure as a transported-loop computation. It remains a numerical transported-loop receipt, not a symbolic pullback proof.

### V2 - Round-Trip Gates And Mutation Controls

Status: **PASS for the v1 fail condition.**

The v2 `round_trip_report` differentiates the symbolic `z_dot` rows back to exported `A*r+b`, checks finite-time affine flow derivatives against the generator, and reruns stored `Phi_D/Phi_I` map rows. The fresh in-memory rerun matched the stored report:

```text
symbolic_z_dot_residuals_zero = true
finite_time_derivative_max_error = 1.314588836351091e-10
finite_time_derivative_sample_count = 120
loop_order_map_recompute_max_error = 5.714040351989524e-13
loop_order_map_recompute_sample_count = 60
pass = true
```

The negative-control table now has 18 controls with `executed=true`, `computed_mutation=true`, `mutation_rerun_through_same_gate=true`, `gate_passed_after_mutation=false`, `expected_failure_observed=true`, and non-empty failing values. Spot-checked failing values include:

```text
C03_inner_outer_loop_swap: phase_sensitive_rows=14, rows_changed_before_mutation=14, rows_changed_after_swap_label_mutation=0
C10_wrong_H_R_sign: max_A_difference_vs_exported_Ne_Spiral_R=2.309401076758503
C11_wrong_Si_frame: max_A_difference_vs_exported_Si_Citadel_R=0.4
C12_loop_order_label_gap: computed_g_DI_rows=0, required_rows=20
C15_noncommuting_control_erasure: actual_max_g_DI=0.36341316691657366, label_only_g_DI=0.0
C17_cross_engine_disagreement_tolerated: fatal_gate_match_after_perturbation=false
```

This closes the v1 K5 failure. The controls are still compact gate-rerun receipts rather than full duplicate packet artifacts, but they now carry computed failing values and the in-memory result rebuild reruns the gate logic cleanly.

### V3 - Generic `chi0` Repin

Status: **PASS.**

The claim path is repinned to `chi0=pi/7`; source/result search found `chi0=pi/8` only in the older v1 audit text and in the validator's stale-pin rejection check. The v2 genericity report passes:

```text
sin_2chi0 = 0.7818314824680298
cos_2chi0 = 0.6234898018587335
sin_2chi0_minus_cos_2chi0 = 0.15834168060929626
sin_2chi0_plus_cos_2chi0 = 1.4053212843267633
no_special_trig_zeros = true
required_phase_rows_visible = true
```

Loop-swap sensitivity is restored on the phase-dependent rows:

```text
Ne_Vortex_L max_abs_inner_minus_outer = 1.1488001584836767
Ne_Spiral_R max_abs_inner_minus_outer = 1.1488001584836767
Se_Funnel_L max_abs_inner_minus_outer = 0.22976003169673534
Se_Cannon_R max_abs_inner_minus_outer = 0.22976003169673534
Ni_Pit_L max_abs_inner_minus_outer = 0.2297600316967352
Ni_Source_R max_abs_inner_minus_outer = 0.2297600316967352
Si_Citadel_R max_abs_inner_minus_outer = 1.9649568333334237
Si_Hill_L phase_dependent = false, max_abs_inner_minus_outer = 0.0
```

### V4 - Stable Values And Blind Formula Repin

Status: **PASS on the available audit surface.**

No superseded v1 result JSON is retained in the packet; the only available v1 comparison surface is the prior audit text plus stable source/result fields. On that surface, values not affected by `chi0` remained stable:

```text
g_DI first sample = 0.35423441716684667
prior audit recorded sample = 0.35423441716684667
g_DI max = 0.36341316691657366
placement_count = 16
matrix64_overlay_count = 64
Ne_Vortex_L z_dot = -2*sqrt(6)*sin(2*eta)*cos(2*chi + pi/4)/3
Ne_Spiral_R z_dot = 2*sqrt(6)*sin(2*eta)*cos(2*chi + pi/4)/3
Si_Hill_L z_dot = 0
Si_Citadel_R z_dot = 2*sin(2*chi)*sin(2*eta)/5 - 2*cos(2*eta)/5
```

Repin-affected leakage values match the blind formulas evaluated at `chi0=pi/7`:

```text
Ne_Vortex_L, eta=pi/4:
expected L_inner = 4*sqrt(6)*pi*sin(pi/28)/3 = 1.1488001584836767
recorded L_inner = 1.1488001584836767
abs_delta = 0.0

Ne_Spiral_R, eta=pi/4:
expected L_inner = -4*sqrt(6)*pi*sin(pi/28)/3 = -1.1488001584836767
recorded L_inner = -1.1488001584836767
abs_delta = 0.0

Si_Citadel_R, eta=pi/4:
expected L_inner = 4*pi*sin(2*pi/7)/5 = 1.9649568333334237
recorded L_inner = 1.9649568333334237
abs_delta = 0.0
```

Cross-engine signatures match exactly across Julia/JAX/PyTorch for the scaled leakage rows, placement count, Matrix64 overlay count, and `loop_order_g_DI_scaled_1e9=363413167`.

Final line: **EARNED** against the v1 reject conditions, at scratch-diagnostic ceiling only.

## 2026-06-10 Remediation Note - Tooling Step 4

Scope: audit queue item 4, flow-evolution claim-path remediation for `geo_s6_stacked_flows_hopf_v0`.

Route table:

```text
Julia canon leg: DifferentialEquations.ODEProblem + DifferentialEquations.solve(Tsit5) for the S6 loop-order flow matrices.
JAX shell/eta leg: diffrax.ODETerm + diffrax.diffeqsolve + diffrax.Tsit5 over exported S5 affine ODE rows, batched per terrain row.
JAX loop leg: diffrax.ODETerm + diffrax.diffeqsolve + diffrax.Tsit5 for Phi_D/Phi_I loop-flow matrices.
Exact special-case checks: LinearAlgebra.exp / jax.scipy.linalg.expm retained only as exact constant-flow parity checks.
```

Byte-stability: claim values are unchanged against `HEAD` for `pin_spec`, `pin_sha256`, `convention_pin`, `terrain_summary`, `terrain_action_rows`, `matrix64_overlay_rows`, `cross_engine_consistency`, `shell_leakage_rows` excluding newly added `flow_solver_route`, `loop_order_gap` claim values, `placement_rows` excluding fresh receipt hashes, `positive_ledger` pass bits, and `divergence.max_divergence`. The P10 strength token was intentionally relabeled from matrix-exponential route wording to `flow_solver_with_exact_matrix_exponential_check`.

Fresh rerun and validators:

```text
geo_s6_stacked_flows_hopf_v0_julia.jl: ok=true
geo_s6_stacked_flows_hopf_v0_jax.py: ok=true
geo_s6_stacked_flows_hopf_v0_pytorch.py: ok=true
geo_s6_stacked_flows_hopf_v0_envelope.py: ok=true
geo_s6_stacked_flows_hopf_v0_exact_strength_validator.py: ok=true, errors=[]
scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed .../geo_s6_stacked_flows_hopf_v0_envelope_results.json: ok=true
```

Capability gate: changed-file gates returned no violations for `sim_diffrax_capability.py`, `sim_differentialequations_capability.py`, `sim_symbolics_capability.py`, `geo_s6_stacked_flows_hopf_v0_jax.py`, `geo_s6_stacked_flows_hopf_v0_julia.jl`, and `geo_s6_stacked_flows_hopf_v0_envelope.py`.
