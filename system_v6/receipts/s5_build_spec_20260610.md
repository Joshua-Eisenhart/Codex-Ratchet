# S5 build spec prep - terrain generator flow packet - 2026-06-10

Status: read-lane spec only, not a build. Deliverable target for a future builder: one bounded S5 packet for genuinely new terrain-generator flow receipts only.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not claim canonical terrain-family completion, Axis-level admission, runtime closure, engine closure, physics, or a completed constraint manifold.

## Stage anchor

The canonical geometry program puts S5 after S4 operators and before S6 stacked terrain/operator/Hopf geometry. S5 scope is: `D[L]`; the eight terrain generators `X_{a,s}`; `H_L=+H0`, `H_R=-H0`, `H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)`; flows `exp(tX)`; CPTP/trace/positivity at every `t`; fixed points and basins per flow; purity preservation for pure-Hamiltonian flows; non-unitality witnesses (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:16-22`).

Binding stack rule: this packet lives on the density/Bloch quotient. It may cite S1/S2/S3 for convention and quotient boundaries, but it does not prove spinor phase, Hopf holonomy, terrain/operator stacking, 64-cell runtime closure, or induced-geometry ratcheting.

## Already computed - cite, do not rebuild

1. The terrain source laws are on file.
   - `system_v5/READ ONLY Reference Docs/terrain math.md:70-90` defines `D[L]`, the eight generator rows, and the Si projector rows.
   - `system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md:45-71` defines `H0`, `H_L/H_R`, left/right Bloch Hamiltonian signs, the eight stage generators, and `Phi_tau^s(t)=e^{tX_tau^s}`.

2. `terrain_generator_sheet_packet` already source-locks and computes finite-time channel forms.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:48-99` records source refs, source-lock hashes, and pins including `H0`, `H_L`, `H_R`, `eps`, `gamma_Ni`, `kappa_Si`, `omega_Si`, and z/x Si frames.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:191-208` defines Pauli matrices, `sigma_-`, `sigma_+`, `H0`, and z/x projectors.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:371-419` implements the eight source-locked generator functions plus controls.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:442-447` computes finite-time channels as `expm(t * superoperator(X))`.
   - `system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json:24` has `all_pass=true`; `:2584`, `:4678`, and `:4999` preserve the scratch ceiling.
   - Reuse these forms and pins. Do not regenerate or relabel the existing packet.

3. `terrain_generator_sheet_packet` already has finite-time CPTP-style checks, weak fixed/strata checks, pair separation, placement rows, and non-unitality columns.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:1000-1005` attaches channel certificates and unitality rows.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:1025-1135` computes fixed-point/strata checks for Pit/Source/Hill/Citadel and terrain pair separation.
   - `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:1125-1150` gates CPTP, fixed, pair, placement, negative, SMT, state, and source-lock passes.
   - `system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json:2957,3018,3079` records `fixed_pass=true` across engines.
   - `system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json:5270-5271,5550-5551,5830-5831` records `ni_pair_non_unital=true` and `non_ni_unital=true`.
   - These are finite-time/source-lock receipts and weak fixed/strata evidence. They are not the new per-generator fixed-point/basin proof packet.

4. The terrain packet audit already adjudicated the current evidence and caveats.
   - `system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md:3-20` calls the packet genuine-with-caveats and records the validator result.
   - `system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md:24-42` adjudicates source-lock fidelity for Ni and Si rows.
   - `system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md:67-78` says pure Ne is source-forced and weak-dissipator Ne is an exploratory pinned variant.
   - `system_v6/sims/terrain_generator_sheet_packet/audit_verdict.md:121-130` lists hardening needs: per-family pinned-choice metadata, stronger SMT derivation labels, source freshness, unitality column, Axis-0 sign pattern, and entropy columns.
   - Bind those caveats. The S5 flow packet must not silently promote the old packet to exact basin proof.

5. Matrix64 already computed finite-time terrain/operator flow applications.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:11-13` preserves the scratch ceiling.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:28-38` confirms 64 rows with ordered outputs, `Delta_T_O_matrix_plus_minus`, norms, observables, trajectory, fingerprint ladder, and a source-token caveat now closed by transitive-source surfacing.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:76-99` adjudicates F7 trajectory distinctness and manual commuting/noncommuting cells.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:117-144` records post-hardening closure and fresh validators.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json:5593-31413` contains the matrix rows and ordered output surfaces.
   - S5 may cite these as finite-time applications/order-gap context only. Do not rerun Matrix64.

6. S4 v2 gives binding process lessons for exact flow/basin work.
   - `system_v6/sims/geo_s4_operator_stage_v0/build_card.md:23-29` requires primary convention pins, iterated basin/orbit receipts, executed mutation controls, Julia derivation from density/channel forms, and honest SMT scope.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:326-340` says v2 closed basin gaps by adding explicit iteration formulas and computed limit/non-limit receipts.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:342-374` says v2 controls are executed mutations and SMT is correctly scoped as pinned-entry contradiction, not full symbolic proof.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:357-365` says Julia now derives density/channel rows from forms.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:376-398` preserves strength tokens and ceilings.
   - S5 must carry these lessons forward. Prose basin classifications are not enough.

## Genuinely new S5 work

Build only these new receipts:

1. Exact Bloch generator table for the eight terrain flows.
   - Emit `r'(t)=A r(t)+b` for all eight generators in the source-locked standard Bloch basis.
   - Include symbolic parameters first: `lambda_Se_L/R`, `epsilon_Se_L/R`, `gamma_Ni_L/R`, `epsilon_Ni_L/R`, `kappa_Si_L/R`, `omega_Si_L/R`, with the packet pins as a second row.
   - Include `H_L=+H0`, `H_R=-H0`, `H0=n.sigma`, `n=(1,1,1)/sqrt(3)` for rows using `H_L/H_R`.
   - For Si, keep the packet's z/x projector-retention frames explicit: Hill uses the z frame; Citadel uses the x frame. If a builder tries to replace these with `H0` frames, the pin gate must fail.
   - Record source-derived caveats for Se coefficient sets and Ne weak-dissipator variants. Pure Ne is the S5 purity-preservation object; weak Ne is optional context only unless explicitly scoped.

2. Exact flow solutions `r(t)` for each row, where closed-form is honest.
   - For pure Hamiltonian Ne rows, emit Rodrigues rotation about `n`:
     `r(t)=R_n(+2t)r0` for L and `r(t)=R_n(-2t)r0` for R, or `+/-2 epsilon t` if the builder scopes an epsilon parameter.
   - For isotropic Se source rows, if the exact source row is `lambda sum_{j=x,y,z}D[sigma_j] - i epsilon[+/-H0,.]`, emit `r(t)=exp(-4 lambda t) R_n(+/-2 epsilon t) r0`. If the source-locked packet row uses a pinned non-isotropic Pauli coefficient family, emit the exact `A` and `exp(tA)` for that actual row and mark the source-vs-pin difference.
   - For Ni rows, emit the affine solution `r(t)=r_* + exp(tA)(r0-r_*)`, with `r_*=-A^{-1}b` when invertible, plus exact pinned-row values. Do not replace this with sample convergence.
   - For Si z/x rows, emit damped rotation closed forms. Hill should have `z(t)=z0` and damped spiral in `(x,y)`; Citadel should have `x(t)=x0` and damped spiral in `(y,z)`.
   - Every solution row must include its generator matrix `A`, affine vector `b`, eigenvalue/decay notes, and exact/pinned consistency checks.

3. CPTP, trace, Hermiticity, and positivity proof boundary for every `t>=0`.
   - The main proof path is GKSL form plus exact finite-dimensional generator construction, not a finite sample grid.
   - Still include sampled Choi/trace-preservation checks at `t in {0, 0.1, 0.2, 0.4, 1.0}` as regression fixtures.
   - A sampled check may catch bugs but cannot be the only proof for "every `t`".

4. Fixed points and basins per flow, with iterated/continuous-time limits.
   - Solve `A r + b = 0` inside the Bloch ball for every generator.
   - Emit stability/eigenvalue classification for each fixed set or fixed point.
   - Emit `lim_{t->infty} r(t)` or a non-limit/orbit receipt for every initial condition class.
   - For Se with positive isotropic dissipation, expected fixed point is `r=0` and basin is the whole Bloch ball. If a pinned anisotropic Se row changes this, preserve the divergence and mark blocked pending audit.
   - For pure Ne, expected fixed set is the Hamiltonian axis `span(n)` inside the ball. Non-axis points are non-attracting unitary orbits; do not call them basins except as invariant orbit classes.
   - For Ni with positive amplitude damping and Hamiltonian tilt, expected fixed point is the unique affine stationary state; expected basin is the whole Bloch ball. Also include erased-H controls where the dissipator target is the pure z pole.
   - For Si with positive dephasing, expected fixed set is the retained projector axis; basin slices are all states with the same retained axis coordinate.

5. Purity preservation for pure-Hamiltonian flows.
   - Prove `d/dt ||r(t)||^2 = 0` for `Ne/Vortex` and `Ne/Spiral` pure Hamiltonian rows.
   - Include a pure-state boundary fixture with `||r0||=1` and exact `||r(t)||=1`.
   - Include a mixed-state fixture showing spectrum preservation, not just pure-state radius preservation.
   - Include a negative control where a weak dissipator is added and purity preservation fails.

6. Non-unitality witnesses.
   - Emit infinitesimal witnesses `X(I) != 0` for Ni/Pit and Ni/Source, with sign and sigma convention pinned.
   - Emit finite-time witnesses `Phi_t(I)-I != 0` for `t>0` and show `b_t = integral_0^t exp((t-s)A)b ds` is nonzero.
   - Emit `X(I)=0` and `Phi_t(I)=I` for Se, pure Ne, and Si rows under the scoped source/pin assumptions.
   - Preserve the terrain packet's prior non-unitality columns as source evidence, not as the new proof.

7. Quotient-erasure and convention boundary.
   - State that this S5 packet operates on one-qubit density/Bloch terrain flows.
   - It sees affine Bloch flow, Lindblad generator structure, fixed points, basins, unitality, purity, and finite-time channel action.
   - It does not see global spinor phase, Hopf fiber holonomy, S6 stacked placements, Matrix64 closure, or induced geometry on survivor sets.

## Proposed packet boundary

Suggested sim id: `geo_s5_terrain_generator_flows_v0`.

Allowed output path for the future build:
`system_v6/sims/geo_s5_terrain_generator_flows_v0/`

Required files for the future build:
- `build_card.md`
- `geo_s5_terrain_generator_flows_v0_julia.jl`
- `geo_s5_terrain_generator_flows_v0_jax.py`
- `geo_s5_terrain_generator_flows_v0_pytorch.py`
- `geo_s5_terrain_generator_flows_v0_envelope.py`
- `geo_s5_terrain_generator_flows_v0_exact_strength_validator.py`
- `results/geo_s5_terrain_generator_flows_v0_{julia,jax,pytorch,envelope}_results.json`
- optional `audit_verdict.md` only after a separate audit lane runs

Do not edit or regenerate the already-computed terrain-generator sheet, Matrix64, S4, S1, or source-lock packets.

## Positive ledger

The future build passes only if the envelope proves all of these:

1. `P1_source_lineage_and_pins`: cites source terrain rows, terrain packet source locks, S1/S4 convention pins, and Matrix64 context without rebuilding them.
2. `P2_exact_bloch_generator_table`: all eight terrain generators have exact `A,b` rows under symbolic parameters and pinned rows.
3. `P3_flow_solutions_exact`: every flow has an exact solution form, with closed forms where honest and `exp(tA)` affine form where that is the exact representation.
4. `P4_cptp_all_t_proof`: every row is proven trace-preserving, Hermiticity-preserving, positive/CPTP for all `t>=0` from GKSL structure, with sampled Choi fixtures as checks only.
5. `P5_fixed_points_exact`: every row solves `A r + b = 0` with exact fixed point/fixed set inside the Bloch ball.
6. `P6_basin_limits_exact`: every row has an explicit `t->infty` limit, basin slice, or non-attracting orbit/non-limit receipt.
7. `P7_pure_hamiltonian_purity_preserved`: pure Ne L/R preserve spectrum and pure-state purity exactly.
8. `P8_nonunitality_witnesses`: Ni L/R have `X(I) != 0` and finite-time `Phi_t(I)-I != 0`; non-Ni scoped rows pass `X(I)=0`.
9. `P9_executed_negative_controls`: all controls are actual mutation reruns with failing values, not declarative booleans.
10. `P10_claim_ceiling`: result carries `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Negative controls

The future build must include controls that can fail:

1. Wrong Hamiltonian sign: set `H_R=+H0`; right Ne/Se/Ni handedness and source-lineage gates must fail.
2. Wrong Bloch convention: flip `sigma_y` without the explicit S1/S4 conversion layer; Hamiltonian rotation signs must fail.
3. Si wrong-frame mutation: use `H0` or z frame for both Si rows; Hill/Citadel fixed-axis and retention rows must fail.
4. Ni sign/jump swap: swap `sigma_-` and `sigma_+`; non-unitality sign and fixed-point target controls must fail.
5. Fake unital Ni: force `b=0` for Ni; `X(I) != 0`, `Phi_t(I)-I`, and basin fixed point gates must fail.
6. Fake non-unital Se/Ne/Si: inject a nonzero affine shift into a unital row; unitality and fixed-point gates must fail.
7. Hamiltonian-as-attractor error: classify pure Ne non-axis orbits as attracting basins; orbit/non-limit gate must fail.
8. Sample-only CPTP proof: remove GKSL/all-`t` proof and leave only Choi samples; `P4_cptp_all_t_proof` must fail.
9. Prose-only basin proof: remove iterated/continuous limit formulas and leave fixed-point prose; `P6_basin_limits_exact` must fail.
10. Source echo: copy the terrain packet's existing fixed/strata rows without deriving `A,b`, solutions, and limits; exactness gates must fail.
11. Weak-Ne promotion: use the weak-dissipator Ne variant as the purity-preservation object; purity gate must fail or mark the row out of scope.
12. Matrix64 conflation: cite Matrix64 ordered applications as proving S5 fixed points/basins; boundary gate must fail.

## Blind list for audit lane

Keep these as audit expectations. A builder may encode them only as generated results from exact derivation, not as hand-entered verdicts.

1. Pure `Ne/Vortex` and `Ne/Spiral` are unitary Hamiltonian flows with opposite handedness around `n=(1,1,1)/sqrt(3)`.
2. Pure Ne preserves Bloch radius, spectrum, entropy, and pure-state purity; it has no attracting basin off the Hamiltonian axis.
3. If Se is the source isotropic `sum_j D[sigma_j]` row with positive `lambda`, its Bloch flow is contraction plus rotation, fixed point `r=0`, whole-ball basin.
4. If the existing packet's pinned Se coefficient family differs from the full source isotropic row, the result must name the divergence instead of smoothing it.
5. Ni/Pit and Ni/Source are the non-unital pair; their affine vectors have opposite z-pole signs under the locked sigma convention.
6. Ni with Hamiltonian tilt has a unique stationary state when the damping rate is positive; erased-H controls recover pure z-pole dissipator targets.
7. Si/Hill retains the z-axis and damps transverse coherence with possible z-frame rotation.
8. Si/Citadel retains the x-axis and damps transverse coherence with possible x-frame rotation.
9. Unital rows have `X(I)=0` and `Phi_t(I)=I`; Ni rows do not.
10. Fixed-point claims and basin claims are different. A fixed set without a limit/orbit receipt is not a basin proof.
11. Continuous-time `t->infty` basins are not the same object as discrete S4 iterated-channel basins, but the S4 v2 receipt pattern is binding: explicit formula, computed pins, and non-limit controls.
12. Every sampled numerical check is subordinate to the exact symbolic/GKSL/affine proof path.

## Audit attacks

Audit the future packet against these failure modes:

1. Source-lock theater: hashes and citations are present but the `A,b` table is hand-written or copied.
2. Convention drift: the result changes the Pauli/Bloch y sign or active/passive rotation convention without a declared conversion row.
3. Pin collapse: the result proves only packet pins and omits symbolic parameter conditions such as zero damping, positive damping, and pure-Hamiltonian limits.
4. Flow/sample confusion: the result verifies `t=0.4` channels and calls that an all-time flow proof.
5. Fixed-point/basin collapse: the result solves `A r+b=0` but does not prove convergence, nonconvergence, or basin slices.
6. Hamiltonian attraction hallucination: pure unitary orbits are called attractors.
7. Non-unitality sign error: Pit/Source signs are swapped because `sigma_-` labels are read semantically instead of from the locked matrix convention.
8. Weak variant creep: exploratory weak-dissipator Ne rows are silently treated as source-forced pure Ne.
9. Declarative controls: controls only say `detected=true` without mutation inputs, mutated outputs, and failing gates.
10. Tool overclaim: SMT checks bind computed entries but are described as full symbolic derivations.
11. Engine-role blur: PyTorch hardcoded/pinned mirrors are treated as symbolic CAS evidence.
12. Matrix64/S6 bleed-through: terrain/operator order gaps or 64-cell distinctness are used as S5 flow fixed-point evidence.
13. Ceiling creep: result says canonical terrain claim, formal admission, completed terrain family, or runtime closure.

## Directive rules binding

1. Build genuinely new S5 receipts only. Cite existing source locks, terrain packet rows, Matrix64 applications, and S4 v2 lessons.
2. Use source-locked standard Bloch convention as primary, with any S1/S4 conversion layer explicit.
3. Derive exact `A,b` and flow solutions before evaluating pins.
4. Separate fixed points, basin limits, invariant orbits, and non-limit behavior.
5. Use GKSL/all-`t` reasoning for CPTP claims; sampled Choi checks are regression fixtures only.
6. Keep pure Ne separate from weak-dissipator Ne variants.
7. Every result must include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, source lineage, exactness labels, executed can-fail controls, and claim ceiling.
8. If symbolic derivation and prior terrain packet/Matrix64 evidence disagree, preserve the divergence and mark the packet blocked pending audit. Do not smooth it into agreement.
