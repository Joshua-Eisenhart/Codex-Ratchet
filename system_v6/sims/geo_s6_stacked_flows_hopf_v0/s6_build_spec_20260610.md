# S6 build spec prep - stacked terrain/operator/Hopf geometry - 2026-06-10

Status: read-lane spec only, not a build. Deliverable target for a future builder: one bounded S6 packet for genuinely new RESTRICTED/STACKED-mode geometry receipts only.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not claim canonical stacked geometry, Axis admission, runtime closure, physics, engine closure, or a completed constraint manifold.

## Stage anchor

The canonical geometry program puts S6 after S2 connection/flux/foliation, S4 operators, S5 terrain flows, and Matrix64 terrain/operator precedence. S6 scope is: `Phi(T_eta)` preserve/move/leave plus `dz/dt` leakage; terrain action on `A`, `F`, `h`, and `Phi_ij`; the 16 placements `(X_{a,s}, Y_l)`; order gaps `Delta_{T,O}`; the 64 composite cells; and loop-order `Phi_D=UEUE` versus `Phi_I=EUEU` (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:10-22`).

Binding mode: this is the first RESTRICTED/STACKED-mode stage. Use mode 2 of the stacking law: maps from a higher layer are confined to lower structures and classified as preserve / move-to-other-leaf / leave-foliation, with shell leakage measured (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:10-14`). The nesting-law receipt's arrow discipline binds: every map must name its arrow type, and `S^3 = union_eta T_eta` is a foliation arrow, not a generic quotient or runtime label (`system_v6/receipts/nesting_law_audited_20260610.md:28-42`).

Use `z = cos(2 eta)` as the shell coordinate inherited from S1/S2. The S6 leakage object is `dz/dt` on `T_eta` induced by exported terrain generators. Leakage integrals are the flux layer for this restricted-mode packet. Do not introduce a separate, competing "flux" object.

## Already computed - cite, do not rebuild

1. S2 connection/flux/foliation is earned.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:17-19` earns the positive S2 scratch diagnostic and preserves the ceiling.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:35-63` verifies the holonomy convention map and genuine horizontal transport.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:65-101` verifies `A`, `F=dA`, Stokes, and Chern rows.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:103-131` verifies `T_eta`, double-cover area, grid accounting, shell rows, and adjacency flux.
   - S6 must cite these `A/F/h/T_eta` receipts. Do not rebuild S2.

2. S4 operator-channel lessons are binding.
   - `system_v6/sims/geo_s4_operator_stage_v0/build_card.md:23-29` requires explicit convention pins, basin/orbit receipts, executed mutation controls, Julia density/channel derivation, and honest SMT scope.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:326-340` closes basin gaps by explicit iteration formulas and computed limits.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:342-374` closes executed-control and SMT-scope gaps.
   - `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:376-398` preserves strength tokens and ceilings.
   - S6 inherits these process gates. A classification table without round-trip and mutation evidence is not enough.

3. S5 v2 terrain-flow rows and exported `A,b` are computed.
   - `system_v6/sims/geo_s5_terrain_flows_v0/build_card.md:18-28` defines the v2 rebuild gates: symbolic/differentiated `A,b`, flow round trips, fixed-set consistency, basin/orbit consistency, executed controls, and cross-engine fatality.
   - `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:326-365` closes the pure `Ne` exported `A` bug and verifies nonzero Hamiltonian precession rows.
   - `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:361-410` closes flow round-trip, fixed-set, and basin/orbit consistency from exported `A,b`.
   - `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:412-446` closes executed controls and cross-engine pinned `A,b` agreement, with the scratch ceiling preserved.
   - S6 must consume the exported S5 `A,b` rows. Do not derive a second S5 table unless an import/hash mismatch blocks the packet.

4. Matrix64 already computed the 64 chart cells and terrain/operator order gaps.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:9-13` admits the 64-cell chart matrix only as a genuine scratch diagnostic.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:26-32` verifies 64 rows with ordered outputs, `Delta_T_O`, behavior columns, and chart/runtime boundary.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:76-99` verifies the named `F7_trajectory=64` result and manual commuting/noncommuting cells.
   - `system_v6/sims/terrain_operator_precedence_64_matrix/audit_verdict.md:119-150` records post-hardening closure, stable fingerprint ladder, source-backed validator passes, and ceiling.
   - S6 may join against Matrix64 cell ids and cite its `Delta_T,O` rows. Do not recompute the 64 base cells or relabel Matrix64 as stacked Hopf leakage.

5. The 16 placement grammar exists as source math, not as the new S6 computed pairing receipt.
   - `system_v5/READ ONLY Reference Docs/terrain math.md:72-90` defines the eight terrain generators.
   - `system_v5/READ ONLY Reference Docs/terrain math.md:118-150` lists the full 16 placements and separates generator, loop field, and placement.
   - `system_v5/docs/ENGINE_MATH_REFERENCE.md:99-137` defines `Y_in`, `Y_out`, density visibility, and terrain/loop/placement separation.
   - `system_v5/docs/ENGINE_MATH_REFERENCE.md:145-169` lists the Type 1 and Type 2 placement rows.
   - S6 must compute the placement pairings with exported S5 `A,b` and S2 shell geometry. Do not merely copy the placement table.

6. Loop-order map language exists, but the S6 loop-order gap on the shared carrier is new.
   - `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/geometry-sim-program-canonical-2026-06-10.md:2028-2054` gives `Phi_D=U o E o U o E`, `Phi_I=E o U o E o U`, and the order-gap shape.
   - This is source language for the future S6 loop-order packet. It is not an executed `g_DI` receipt yet.

## Genuinely new S6 work

Build only these new receipts:

1. Shell-leakage classification per S5 flow.
   - Import the earned S5 v2 exported `A,b` rows.
   - Parameterize the Hopf/Bloch latitude by `r_eta(chi)=(sin(2 eta) cos(2 chi), sin(2 eta) sin(2 chi), cos(2 eta))`.
   - Compute `z_dot_X(eta, chi) = e_z^T (A r_eta(chi) + b)` for every terrain flow.
   - Classify each flow on each shell as:
     - `preserve_T_eta`: finite-time image remains on the same Hopf torus; requires `z_dot=0` and pure-state/purity preservation on the shell, not just label agreement.
     - `projected_shell_preserve_but_Hopf_leave`: `z_dot=0` but the density leaves the pure Hopf torus, e.g. contraction/dephasing.
     - `move_leaf`: `z_dot` is independent of loop phase on the shell and moves the full shell coherently to another shell under the finite-time map.
     - `cross_shell`: `z_dot` depends on `chi` or loop position, so one shell shears/crosses multiple shell coordinates.
     - `leave_foliation`: the finite-time terrain flow leaves the pure `S^3`/Hopf-torus foliation even if its density projection remains CPTP inside the Bloch ball.
   - Emit both instantaneous `z_dot` and finite-time `z(t)`/classification where the S5 flow formula allows it.
   - Keep shell leakage separate from purity leakage, but record both.

2. Leakage integrals as the S6 flux layer.
   - For every terrain row and every tested shell, compute loop integrals:
     - `L_inner(X,T_eta)=int_{Y_in loop} z_dot_X(eta, chi(u)) du`;
     - `L_outer(X,T_eta)=int_{Y_out loop} z_dot_X(eta, chi(u)) du`.
   - Because `Y_in` is density-stationary and `Y_out` traverses base phase, the two integrals must be separately computed and separately named.
   - Also compute shell-average leakage `bar_L_X(eta)=(1/2pi) int_0^{2pi} z_dot_X(eta, chi) dchi`.
   - If a flow leaves the pure Hopf foliation, keep the leakage integral as the measured lower-structure flux and mark `A/F/h` pullback claims out of scope unless an explicit mixed-state lift is provided.
   - Positive gates must assert that the leakage integral used for S6 flux is derived from exported `A,b`, not from hand-entered expected signs.

3. Terrain action on `A`, `F`, `h`, and `Phi_ij`.
   - For pure-preserving lifted rows, compute the actual pullback/Lie action on S2 geometry:
     - `Phi_T^* A - A`;
     - `Phi_T^* F - F`;
     - `h(Phi_T(T_eta)) - h(T_eta)` under the S2 convention pin;
     - induced shell-transition map `Phi_ij` between tested `T_eta_i` and `T_eta_j`, when a coherent shell map exists.
   - For nonunitary rows that leave pure `S^3`, compute only the projected density action and the leakage/flux integral, then explicitly mark `A/F/h` as `undefined_without_mixed_lift`.
   - Do not silently use Uhlmann holonomy, mixed-state purification, or a new connection. A mixed lift is out of scope unless separately specified and negatively controlled.
   - Every `A/F/h/Phi_ij` row must cite the S2 convention pin and state whether it is a pure-Hopf action, projected-density action, or undefined.

4. Computed 16 placement pairings.
   - Build the 16 computed rows `(X_{a,s}, Y_l)` from the placement source table, S5 exported `A,b`, and S2/S1 loop fields.
   - Each row must include:
     - `placement_id`, `terrain_id`, `sheet`, `loop_id`, and source path;
     - loop field (`Y_in` or `Y_out`) and density visibility;
     - imported S5 `A,b` hash/row id;
     - `z_dot(eta, chi)` formula;
     - inner/outer leakage integral result;
     - shell classification;
     - `A/F/h` action status;
     - controls showing that swapping `Y_in/Y_out` changes the relevant density-visible rows.
   - Do not treat "16 placements" as the same object as Matrix64's 64 signed terrain/operator cells or older 16 ordered tokens.

5. S6 overlay on Matrix64, without rebuilding Matrix64.
   - Join Matrix64 rows by `terrain_id` and `signed_operator_id` to the new S6 shell-leakage and placement rows.
   - Preserve Matrix64 `Delta_T,O` values as already-computed evidence.
   - Emit an overlay table that says, for each terrain family/operator family or sampled cell:
     - Matrix64 order-gap status from existing result;
     - S6 shell-leakage status from new computation;
     - whether the cell's order gap and shell leakage agree, diverge, or are independent observables.
   - If the future builder needs all 64 overlay rows, it must still import Matrix64 rather than recompute it. A smaller bounded overlay is acceptable only if the build card names the sampled cell policy and leaves full overlay as open.

6. Loop-order gap `Phi_D` versus `Phi_I` on a shared carrier with `g_DI`.
   - Define the shared carrier before computing the gap: pure spinor/Hopf carrier if all maps preserve purity, or density/Bloch carrier if the `E` leg is nonunitary. Do not compare maps on different carriers.
   - Define `U` and `E` explicitly from existing S4/S5 source-locked operators/flows. Do not use label words alone.
   - Compute:
     - `Phi_D = U o E o U o E`;
     - `Phi_I = E o U o E o U`;
     - `Delta_DI(x)=Phi_D(x)-Phi_I(x)`;
     - `g_DI(x)=d(Phi_D(x), Phi_I(x))` with at least trace norm on density and, when defined, shell-coordinate/holonomy deltas.
   - Include order controls:
     - commuting/erased control where `g_DI=0` for the right reason;
     - noncommuting control where `g_DI>0`;
     - carrier-mismatch control that fails if `Phi_D` and `Phi_I` are evaluated on different carriers.
   - `g_DI` must be a computed metric row, not a name for the fact that two labels differ.

## Proposed packet boundary

Suggested sim id: `geo_s6_stacked_terrain_operator_hopf_v0`.

Allowed output path for the future build:
`system_v6/sims/geo_s6_stacked_terrain_operator_hopf_v0/`

Required files for the future build:

- `build_card.md`
- `geo_s6_stacked_terrain_operator_hopf_v0_julia.jl`
- `geo_s6_stacked_terrain_operator_hopf_v0_jax.py`
- `geo_s6_stacked_terrain_operator_hopf_v0_pytorch.py`
- `geo_s6_stacked_terrain_operator_hopf_v0_envelope.py`
- `geo_s6_stacked_terrain_operator_hopf_v0_exact_strength_validator.py`
- `results/geo_s6_stacked_terrain_operator_hopf_v0_{julia,jax,pytorch,envelope}_results.json`
- optional `audit_verdict.md` only after a separate audit lane runs

Do not edit or regenerate S2, S4, S5, Matrix64, source-locked terrain/operator packets, or the canonical program receipt.

## Positive ledger

The future build passes only if the envelope proves all of these:

1. `P1_prior_reuse_lineage`: imports/cites S2 `A/F/h/T_eta`, S5 v2 exported `A,b`, Matrix64 rows, and 16-placement source tables without rebuilding them.
2. `P2_arrow_typing_and_mode`: every S6 map declares RESTRICTED/STACKED mode and names the arrow type: foliation, flow, quotient/projection, covering/group quotient, or undefined-without-lift.
3. `P3_z_dot_from_exported_A_b`: every terrain row computes `z_dot=e_z^T(A r_eta+b)` directly from exported S5 `A,b`.
4. `P4_shell_classification`: preserve/move/cross/leave classifications are derived from `z_dot`, finite-time flow, and purity/Hopf-lift status.
5. `P5_leakage_integrals_are_flux`: inner, outer, and shell-average leakage integrals are computed and used as the S6 flux layer; no second flux definition is introduced.
6. `P6_A_F_h_action_status`: terrain action on `A`, `F`, `h`, and `Phi_ij` is computed where pure-Hopf lifting is defined and explicitly blocked where nonunitary rows leave `S^3`.
7. `P7_sixteen_placements_computed`: all 16 `(X_{a,s},Y_l)` rows are computed pairings, not copied placement labels.
8. `P8_matrix64_reuse_not_rebuild`: Matrix64 `Delta_T,O` and 64-cell rows are reused as existing evidence, with an S6 overlay or sampled overlay clearly marked.
9. `P9_loop_order_gap`: `Phi_D`, `Phi_I`, `Delta_DI`, and `g_DI` are computed on one shared carrier with order controls.
10. `P10_round_trip_gates`: leakage formulas, finite-time shell updates, and loop-order closed forms differentiate/apply back to the exported generator or declared map.
11. `P11_consistency_gates`: shell classification, finite-time image, `A/F/h` status, Matrix64 overlay, and loop-order gap cannot contradict each other silently.
12. `P12_executed_mutation_controls`: all negatives are actual mutation computations with observed failing values, not declarative booleans.
13. `P13_cross_engine_fatality`: load-bearing rows agree across Julia/JAX/PyTorch within declared tolerance, and disagreement fails the envelope.
14. `P14_claim_ceiling`: every result carries `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Negative controls

The future build must include controls that can fail:

1. Hardcoded leakage: replace `z_dot` with expected labels rather than `e_z^T(A r+b)`; `P3` must fail.
2. Wrong shell coordinate: use `z=eta` or `z=sin(2 eta)` instead of `z=cos(2 eta)`; leakage and S2 holonomy consistency must fail.
3. Inner/outer loop swap: swap `Y_in` and `Y_out`; density-visibility and leakage-integral rows must fail for outer-sensitive rows.
4. Preserve/cross collapse: classify every `z_dot=0` row as `preserve_T_eta` without checking purity/Hopf lift; pure-foliation classification must fail.
5. Nonunitary Hopf smuggle: compute `Phi_T^* A` for a nonunitary row without a declared lift; `A/F/h` status gate must fail.
6. Uhlmann smuggle: introduce mixed-state holonomy without a separate scoped definition and controls; boundary gate must fail.
7. Matrix64 conflation: treat Matrix64 `Delta_T,O` as proving shell leakage or placement leakage; S6 reuse boundary must fail.
8. Rebuilt Matrix64: recompute 64 cells inside S6 and allow drift from the committed matrix; lineage gate must fail unless explicitly marked blocked.
9. Label-only 16 placements: copy the placement source table with no `z_dot`, loop integral, or S5 `A,b` row id; `P7` must fail.
10. Wrong `H_R` sign: set `H_R=+H0`; shell leakage and cross-engine rows for right-sheet Hamiltonian flows must fail.
11. Wrong Si frame: use the same retained axis for Hill and Citadel; fixed-axis and shell leakage rows must fail.
12. Loop-order label gap: declare `Phi_D != Phi_I` without computing both maps on a shared carrier; `P9` must fail.
13. Carrier mismatch: compute `Phi_D` on spinors and `Phi_I` on densities, or compare pure and mixed carriers without projection; shared-carrier gate must fail.
14. Commuting-control failure: choose commuting maps but get `g_DI>0`; order-control gate must fail.
15. Noncommuting-control erasure: erase the noncommuting order gap by comparing only labels or final address keys; `g_DI` control must fail.
16. Sample-only leakage: classify shells from a few `chi` samples without symbolic/loop-integral proof; exactness gate must fail.
17. Cross-engine disagreement tolerated: allow Julia/JAX/PyTorch to disagree on load-bearing `z_dot` or `g_DI`; cross-engine fatality must fail.
18. Ceiling creep: say stacked geometry is canonical, admitted, complete, physics, or runtime closure; claim-ceiling gate must fail.

## Blind list for audit lane

Keep these as audit expectations. A builder may encode them only as generated results from derivation, not as hand-entered verdicts.

1. Pure `Ne` rows preserve purity but generally do not preserve fixed `z` shells under the `H0=(x+y+z)/sqrt(3)` Hamiltonian; expected `z_dot` contains the `y-x` precession term with opposite L/R signs.
2. `Y_in` is density-stationary; that does not by itself make `X_{a,s}` shell-preserving.
3. `Y_out` changes the density phase along the base loop and must affect loop-integrated leakage when `z_dot` has phase dependence.
4. Se isotropic dissipative rows should generally leave the pure Hopf torus even if their shell-average leakage has simple form.
5. Ni rows should generally be nonunitary, affine, and shell-leaking; their `b_z` sign must follow the locked `sigma_-`/`sigma_+` convention.
6. Si/Hill is expected to retain the z axis in the S5 flow sense, but retaining z under the density projection is not the same as preserving the pure Hopf torus.
7. Si/Citadel is expected to retain the x axis, so z-shell behavior must not be copied from Hill.
8. A zero leakage integral can mean symmetry cancellation, not pointwise shell preservation.
9. `A/F/h` action is defined on the pure Hopf geometry only when the terrain map admits a pure lift; otherwise the honest result is `undefined_without_mixed_lift`.
10. Matrix64's `F7_trajectory=64` is a named chart-fingerprint result; it does not prove S6 leakage, loop placements, or `g_DI`.
11. Matrix64's `Delta_T,O` and S6 `Delta_DI` are different order gaps and must be separately named.
12. `Phi_D=UEUE` and `Phi_I=EUEU` must be executed as maps; spelling the word order is not evidence.
13. `g_DI=0` on a commuting control is a pass only when the maps were actually evaluated and the carrier was shared.
14. The leakage integrals are the flux layer for this restricted-mode packet; importing a second flux vocabulary should be treated as a boundary error unless explicitly reconciled with S2 `F`.

## Audit attacks

Audit the future packet against these failure modes:

1. Source echo: all citations are present, but `z_dot`, leakage integrals, and `g_DI` are copied or hand-written.
2. Arrow-type drift: foliation, quotient, flow, and covering arrows are mixed into one "stack" label.
3. Flux confusion: S2 curvature flux, S6 shell leakage flux, and runtime/chirality flux are collapsed.
4. Purity omission: shell preservation is judged only by `z_dot`, ignoring whether the map leaves pure `S^3`.
5. Lift hallucination: nonunitary density maps are treated as Hopf-bundle automorphisms.
6. Loop blindness: inner/outer placements carry the same rows even where density visibility differs.
7. Placement/count collapse: 16 placements, 16 ordered tokens, and 64 cells are treated as one object because counts are convenient.
8. Matrix64 overclaim: committed 64 cells are used as proof of S6 stacked geometry.
9. S5 overtrust: S5 v2 validator pass is treated as permission to skip round-trip checks in S6.
10. S4 lesson regression: controls say `executed=true` but do not include mutated inputs, observed outputs, and failing gates.
11. Solver decoration: z3/cvc5 checks bind booleans or labels rather than raw scaled leakage/order-gap entries.
12. Engine-role blur: PyTorch pinned mirrors are described as symbolic CAS, or Julia/JAX disagreement is hidden by the envelope.
13. Carrier mismatch: `Phi_D` and `Phi_I` are compared after different projections or on different carriers.
14. Zero-gap overread: `g_DI=0` or leakage integral zero is promoted to equivalence without checking pointwise behavior and controls.
15. Ceiling creep: result says canonical, admitted, complete, runtime, physics, or manifold closure.

## Directive rules binding

1. Build genuinely new S6 receipts only. Cite S2, S4, S5 v2, Matrix64, and placement source tables; do not rebuild them.
2. Use the S5 v2 exported `A,b` rows as the source of terrain leakage. If those rows cannot be imported with current hashes, stop and mark blocked.
3. Use S2's convention pin for every `A/F/h` or holonomy comparison.
4. Treat shell leakage `dz/dt` and its loop/shell integrals as the S6 restricted-mode flux layer.
5. Keep projected density-shell behavior separate from pure Hopf-torus preservation.
6. Every map must name its arrow type and carrier before the result row is admitted.
7. Matrix64 is reused evidence for 64 cells and `Delta_T,O`; it is not S6 leakage evidence.
8. `Phi_D`/`Phi_I` order gaps must be map executions on a shared carrier with computed `g_DI`.
9. Round-trip gates, consistency gates, executed mutations, and cross-engine fatality from S4/S5 v2 are mandatory.
10. Every result must include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, source lineage, exactness labels, can-fail controls, and claim ceiling.
11. If lower receipts and S6 computations disagree, preserve the divergence and mark the packet blocked pending audit. Do not smooth it into agreement.
