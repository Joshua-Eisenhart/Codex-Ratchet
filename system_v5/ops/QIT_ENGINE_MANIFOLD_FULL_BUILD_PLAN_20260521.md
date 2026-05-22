# QIT Engine / Constraint Manifold Full Build Plan

**Created:** 2026-05-21
**Updated:** 2026-05-21
**Status:** HALTED - audit freeze as of 2026-05-22T05:00:34Z
**Companion prompt:** `system_v5/ops/NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md`

## 2026-05-22 Audit Freeze Notice

This plan is no longer an active implementation instruction.

The build is halted by `system_v5/ops/QIT_ENGINE_MANIFOLD_AUDIT_FREEZE_20260522.md` because the current runtime/evidence path allowed operator-axis mapping drift. In particular, recent work treated terrain labels and simplified runtime channels as sufficient where the source docs require chart-locked ordered tokens, Axis 5 family, Axis 6 sign, precedence, loop placement, sheet/type, and class-correct operator/readout semantics.

Do not continue workstreams from this plan until the audit freeze closes. The only admissible work is source-authority audit, runtime-conformance audit, result quarantine classification, and then a repaired runtime plan.

## Purpose

Build the full QIT engine and geometric constraint manifold as executable repo evidence.

This is not a wiki-routing task and not a prose-synthesis task. The target is a source-native runtime that makes the terrain engines, tensor-network dynamics, bridge, Phi0 readout, and attractor-basin admission testable under the repo scout contract.

## Direct Answer To The Current Correction

Yes, the previous full goal was supposed to move toward this. It did not finish it.

What it did achieve:

- shared exact-torch single-qubit QIT runtime;
- schedule-memory phase map;
- bounded adaptive/piecewise basin candidate;
- product-substrate E=16 bridge scout;
- 1D MPS quantum-trajectory Lindblad rung through L=16;
- full runtime trace showing final admission is still blocked;
- MPS bridge-level Phi0 rescue/falsifier showing nonzero but nonseparating mutual information.

What it did not achieve:

- full coupled E=16 entangled dynamics;
- full tensor-network integration across MPS plus PEPS/PEPS3D dynamics;
- L=32/L=64 MPS Lindblad without bond-saturation blocker;
- PEPS/PEPS3D Lindblad dynamics rather than construction-only evidence;
- bridge-level Phi0 separation against controls;
- final geometric constraint manifold admission;
- scale-level real attractor basin admission.

The new goal is therefore not "do the same goal again." It is: preserve the real completed rungs, formally route the newest spectral engine evidence, then attack the remaining blockers in order.

## Current Evidence Ledger

### Formal Evidence Already In `formal_scouts`

These are the current formal anchors:

1. **Runtime consolidation:** `qit_engine_runtime.py` centralizes exact torch terrain, engine, schedule, fixed-point, spectrum, Bloch, and clustering helpers.
2. **Schedule-memory phase map:** `sim_two_root_constraint_schedule_memory_phase_map_probe.py` maps schedule memory over tau, dissipator profile, Hamiltonian direction, and Hamiltonian magnitude.
3. **Adaptive switching:** `sim_two_root_constraint_adaptive_engine_switching_probe.py` finds `schedule_memory_hysteresis_z` as a bounded single-qubit adaptive/piecewise weak-basin candidate.
4. **Coupled E=16 product bridge:** `sim_two_root_constraint_coupled_e16_phi0_bridge_probe.py` builds valid product-substrate bridge candidates but kills the product bridge as a Phi0 separator.
5. **MPS trajectory Lindblad:** `sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py` runs PyTorch-native MPS quantum trajectories through L=16, with dense L=4 replay validation.
6. **Full trace:** `sim_two_root_constraint_full_manifold_runtime_trace_probe.py` emits an admission trace and keeps final admission blocked.
7. **MPS Phi0 rescue/falsifier:** `sim_two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe.py` shows MPS bridge mutual information is nonzero but not separated from shuffled/type-swap controls.
8. **Iter_195 spectral reproduction:** `sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py` formally reproduces the sidequest single-engine spectrum, Choi CPTP check, Type-1/Type-2 noncommutation, sequential-vs-all-at-once Trotter error, and monostable convergence result.
9. **Spectral manifold phase map:** `sim_two_root_constraint_engine_spectral_manifold_phase_map_probe.py` maps the reproduced single-engine spectral diagnostics over 1,080 bounded parameter rows.
10. **Terrain/stage spectral contribution:** `sim_two_root_constraint_terrain_stage_spectral_contribution_probe.py` quantifies remove/duplicate/reorder terrain-stage effects on the slow memory mode. All terrain families suppress the slow mode in the canonical engine, Ni is strongest by removal and duplication tests, and stage placement/order remain load-bearing.
11. **Late Grok 184-194 engine/tensor routing:** `sim_two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe.py` confirms the earlier sidequest batch is useful only for controls and boundaries. It routes threshold sensitivity, random-CPTP coplanarity/memory controls, proper-terrain law reproduction targets, and MPS/PEPS sidequest attempts as superseded context. It confirms all sources are NumPy/SciPy/quimb or Euler/log-only boundary work, so direct formal promotion is blocked.
12. **Late Grok 196-203 engine-spectral routing:** `sim_two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe.py` confirms the newest sidequest batch is useful but NumPy/SciPy-bound and nonpromotional. It routes slow-mode Pauli/eigenvector projection, n-hat alignment, extreme tau scales, and multisite spectral scaling as formal reproduction targets.
13. **Phi0 slow-mode/terrain bridge repair falsifier:** `sim_two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe.py` replays L=16 MPS states and builds an informed bridge from slow-mode projection, n-hat alignment, terrain identity, stage placement, and schedule history. The result remains `open_nonzero_not_control_separated`: canonical MI is `0.039914842216213775`, while terrain-erased control reaches `0.053958495023197106`.
14. **Coupled E=16 runtime slow-mode bridge:** `sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py` moves beyond product-substrate metadata with a bounded dense E=16 pure-state trajectory: two E=8 halves, local terrain trajectory steps, explicit cross-engine bridge gates, runtime `rho_AB` extraction, and Phi0 controls. It reports `bridge_status=rescued_control_separated`, canonical mean `I(A:B)=0.12573777715326687`, max control `type_swap_control=0.12471879666007199`, canonical-minus-max-control `0.0010189804931948765`, no-coupling delta `0.10988579660901507`, and `final_manifold_admission_allowed=false`.
15. **Full manifold trace refresh:** `sim_two_root_constraint_full_manifold_runtime_trace_refresh_probe.py` integrates the coupled E=16 receipt into the full runtime trace. It reports `trace_refresh_status=refreshed_with_coupled_e16_runtime`, `phi0_current_status=weak_coupled_e16_control_separation_bounded_first_rung`, `coupled_e16_canonical_minus_max_control=0.0010189804931948765`, `manifold_admitted=false`, `final_goal_complete=false`, and keeps L32/L64 scaling, PEPS/PEPS3D dynamics, and scale-level basin admission open.
16. **L32 low-bond tensor mitigation:** `sim_two_root_constraint_l32_tensor_mitigation_or_blocker_probe.py` runs a bounded source-native PyTorch L32 MPS trajectory surface at bond cap 4 across all four initial families. It reports `l32_status=bounded_low_bond_l32_surface_complete`, `stages_completed=192`, `families_completed=4`, elapsed `36.91689920425415s`, max bond `4`, total truncation `0.02360643923876433`, max family truncation `0.018405225557571625`, Phi0 mutual-information readouts by family, and keeps L64, PEPS/PEPS3D, scale-level basin, and final manifold admission blocked.
17. **L64 low-bond tensor mitigation:** `sim_two_root_constraint_l64_tensor_blocker_or_mitigation_probe.py` runs a bounded source-native PyTorch L64 MPS trajectory surface at bond cap 4 across all four initial families. It reports `l64_status=bounded_low_bond_l64_first_rung_complete`, `stages_completed=96`, `families_completed=4`, elapsed `73.41843509674072s`, max bond `4`, total truncation `9.417845500992903e-05`, max family truncation `5.516561765594344e-05`, Phi0 mutual-information readouts by family, and keeps full L64 convergence, robust Phi0, full PEPS/PEPS3D, scale-level basin, and final manifold admission blocked.
18. **Small-grid PEPS dynamics:** `sim_two_root_constraint_peps_small_grid_dynamics_probe.py` runs a tiny 2D PEPS-style PyTorch tensor grid with local terrain no-jump steps plus nearest-neighbor SVD gate updates, exact contraction readouts, local/no-dynamics controls, and Phi0 diagnostics. It reports `peps_status=small_grid_peps_dynamic_control_separated`, grid `[2, 2]`, bond cap `2`, dynamic-minus-max-control MI by family with `plus_x=0.0013512574711469463`, max norm error `1.1102230246251565e-16`, finite truncation diagnostic `3.8346987982482204`, and `final_manifold_admission_allowed=false`. This is not PEPS3D, full PEPS convergence, scale-level basin admission, or final manifold admission.
19. **Tiny PEPS3D dynamics:** `sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe.py` runs a tiny 3D PEPS-style PyTorch tensor cube with local terrain no-jump steps plus x/y/z nearest-neighbor SVD gate updates, exact contraction readouts, local/no-dynamics controls, and Phi0 diagnostics. It reports `peps3d_status=tiny_peps3d_dynamic_control_separated`, grid `[2, 2, 2]`, bond cap `2`, dynamic selected-edge MI `plus_x=0.0018790415462067722`, dynamic edge-max MI `plus_x=1.3307868724585188`, max norm error `1.1102230246251565e-16`, finite truncation diagnostic `8.671044423429251`, and `final_manifold_admission_allowed=false`. This is not full PEPS3D convergence, scale-level basin admission, or final manifold admission.
20. **Coupled-E16 Phi0 stress controls:** `sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe.py` replays the bounded dense coupled-E16 runtime across theta values `[0.035, 0.055, 0.075]` and seed offsets `[0, 9973]`, with no-coupling, shuffled pairing, type-swap, random matched-norm, history-erased, slow-mode-erased, n-hat-erased, terrain-erased, weak/strong coupling, shuffled bridge-gate, and tensor-carrier challenge controls. It reports `stress_status=open_nonrobust_internal_controls`, `min_canonical_minus_max_internal_control=-0.13199144731783669`, canonical MI range `[0.06353867860158008, 0.11896471552798837]`, tensor challenge max `peps3d_tiny_edge_max_delta_max=1.3307868724585532`, and `final_manifold_admission_allowed=false`. This demotes the weak coupled-E16 Phi0 rung from weak rescue to open/nonrobust.
21. **Phi0 response-gradient repair after stress:** `sim_two_root_constraint_phi0_bridge_response_gradient_after_stress_probe.py` consumes the coupled-E16 stress surface and tests whether no-coupling response deltas or theta-gradients rescue the bridge. It reports `repair_status=open_nonrobust_response_controls`, canonical mean `I(A:B)=0.09083182167095172`, canonical minimum no-coupling delta `0.013053955645177695`, canonical mean no-coupling delta `0.05526207410925876`, canonical mean absolute gradient `0.7330243954009311`, max comparable delta `terrain_erased=0.1038555286726403`, max comparable absolute gradient `terrain_erased=1.2996814412379643`, max any absolute gradient `weak_coupling=4.729915700344511`, `tensor_carrier_challenge_passed=false`, and `final_manifold_admission_allowed=false`. This keeps the current Phi0 bridge family open/nonrobust rather than repaired.
22. **Full trace after Phi0 stress:** `sim_two_root_constraint_full_manifold_trace_after_phi0_stress_probe.py` refreshes the runtime trace after the stress receipt. It reports `trace_refresh_status=refreshed_after_phi0_stress_controls`, `phi0_current_status=open_nonrobust_internal_controls`, `manifold_admitted=false`, `final_goal_complete=false`, and keeps robust Phi0, full PEPS/PEPS3D, scale-level basin evidence, and final admission blocked.
23. **Axis0 layered entropy-ratchet audit:** `sim_two_root_constraint_axis0_layered_entropy_ratchet_audit_probe.py` makes the Axis0 doctrine split executable. It verifies local doctrine surfaces, builds a monotone layer-to-entropy admissibility matrix, and checks unlock thresholds: `L2` torus-seat chart sign / entropy gradient, `L4` signed bipartite family (`S(A|B)`, `I_c`), `L6` Hopf/Chern support, `L7` schedule-history forms, and `L8` shell-weighted forms. It reports `axis0_entropy_ratchet_status=layered_doctrine_executable`, `current_phi0_failure_reframed_as_layer_mismatch=true`, `recommended_next_bridge_target=L7_Xi_history_or_L8_shell_weighted_phi0`, and `final_manifold_admission_allowed=false`. Grok, Gemini direct API, Sonnet high, and Opus high external audits all returned `support_with_caveats`; the scout now includes an explicit `l4_receipt_promotion_guard` so future promotional L4 receipts cannot be silently routed away.
24. **L7 schedule-history Xi bridge:** `sim_two_root_constraint_l7_xi_history_phi0_bridge_probe.py` builds the first routed L7 bridge packet. It constructs exact torch schedule surfaces over `tau={0.5,1.0}` and schedule word lengths 2-5, maps schedule history into a two-qubit `Xi_history -> rho_AB`, and evaluates `I(A:B)`, `S(A|B)`, and `I_c(A->B)` against no-coupling, history-erased, suffix-erased, type-swap, shuffled-history, and random matched-norm controls. It reports `l7_xi_history_status=open_nonzero_not_control_separated`, canonical mean `I(A:B)=0.009135587590283257`, max control `random_matched_norm_control=0.011937687839140024`, canonical-minus-max-control `-0.002802100248856767`, canonical-minus-no-coupling `0.009135587590283302`, and `final_manifold_admission_allowed=false`. Grok, Gemini direct API, Sonnet high, and Opus external audits all returned `support_with_caveats`. The shared verdict is that L7 is executable but not promotable; Sonnet identified a possible unconditional `theta_base` floor confound, and Opus requires structured adversarial L7 controls before L8. The next bridge target is therefore an L7 theta-base/adversarial-control scout; L8 shell-weighted is gated behind that result.
25. **L7 theta-base/adversarial-control bridge gate:** `sim_two_root_constraint_l7_xi_history_theta_base_and_adversarial_control_probe.py` ablates the unconditional `theta_base` floor and tests canonical L7 history terms against structured controls (`schedule_shuffled`, `time_reversed`, `phase_randomized`, `block_permuted`, suffix/history-erased, type-swap) plus random matched-norm controls over 32 seeds. It reports `l7_theta_adversarial_status=open_nonzero_not_control_separated`, zero-base canonical `I(A:B)=0.002676309726590367`, zero-base canonical-minus-no-coupling `0.002676309726590411`, zero-base max control `time_reversed` with `I(A:B)=0.004576765529614972`, zero-base canonical-minus-max-control `-0.0019004558030246048`, `floor_carries_signal=false`, `l8_shell_weighted_allowed_next=false`, and `final_manifold_admission_allowed=false`. This means the L7 signal is not purely theta-floor carried, but it is still not structure-separated; do not build L8 as bridge evidence unless `Xi` is redesigned or a new L7 family survives stronger controls.
26. **L64 adaptive-bond trajectory batching:** `sim_two_root_constraint_l64_adaptive_bond_trajectory_batch_probe.py` strengthens the L64 tensor route beyond the fixed D=4 first rung. It runs source-native PyTorch L64 MPS quantum trajectories for all four initial families and two seeds with an adaptive SVD cap policy over caps 2 and 4. It reports `l64_adaptive_status=bounded_adaptive_l64_batch_complete`, `trajectory_count=8`, `completed_trajectories=8`, `stages_completed=64`, `cap_values_seen=[2,4]`, `cap_increase_count=2`, `cap_decrease_count=2`, `max_bond_observed=4`, `total_truncation_error=1.4273902332923543e-05`, `norm_error=1.7763568394002505e-15`, family mean center-pair `I(A:B)` values including `plus_x=0.2920463982362539`, and `final_manifold_admission_allowed=false`. This is real adaptive L64 tensor-runtime movement, but still not full L64 convergence, not PEPS/PEPS3D closure, not robust Phi0, and not scale-level basin admission.
27. **Causal-irreversibility `Xi` bridge redesign:** `sim_two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe.py` replaces the failed hand-shaped L7 history scalar with a runtime-derived bridge Hamiltonian from schedule-channel forward/reverse asymmetry, fixed-point Bloch response, and channel noncommutation. It tests `I(A:B)`, `I_c(A->B)`, directional coherent information, and negativity against no-coupling, time-reversed, schedule-shuffled, block-permuted, order-erased, type-swap, causal-erased, phase-randomized, and random matched-norm controls over `tau={0.5,1.0}` and 24 seeds. It reports `xi_causal_irreversibility_status=open_nonzero_not_control_separated`, best metric `I_c_A_to_B`, canonical-minus-no-coupling `I(A:B)=0.00031091535856928954`, canonical-minus-max-control `I(A:B)=-0.00043089567825572674`, coherent-information canonical-minus-max-control `-0.00014006231835850258`, `l8_shell_weighted_allowed_next=false`, and `final_manifold_admission_allowed=false`. This is a genuine bridge redesign attempt, but it still does not unlock L8 or robust Phi0.
28. **L64 adaptive-vs-fixed bond-cap bias sweep:** `sim_two_root_constraint_l64_adaptive_bond_bias_sweep_probe.py` compares fixed D=2, fixed D=4, and adaptive D=2/4 L64 MPS trajectory policies on the same four-family/two-seed rows. It reports `l64_bias_sweep_status=bounded_l64_adaptive_bias_sweep_complete`, `trajectory_count=24`, `completed_trajectories=24`, `stages_completed=192`, policy mean center-pair `I(A:B)` values `adaptive2_4=0.07515230420336619`, `fixed2=0.07515307590557144`, `fixed4=0.07534442198306783`, adaptive mean absolute delta to fixed4 `0.00020854331586046506`, adaptive max absolute delta to fixed4 `0.000657306790395995`, and policy total truncation errors `adaptive2_4=1.4273902332923543e-05`, `fixed2=4.169107486913291e-05`, `fixed4=4.139166310236371e-09`. This bounds cap-policy bias for the one-cycle L64 first rung, but it is still not full L64 convergence, robust Phi0, PEPS/PEPS3D closure, scale-level basin admission, or final manifold admission.
29. **L64 two-cycle fixed/adaptive stability:** `sim_two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe.py` extends the L64 tensor route to two complete cycles, comparing adaptive D=2/4 against fixed D=4 on matched four-family/two-seed rows. It reports `l64_two_cycle_status=bounded_l64_two_cycle_stability_complete`, `trajectory_count=16`, `completed_trajectories=16`, `stages_completed=256`, policy mean center-pair `I(A:B)` values `adaptive2_4=0.06466151342308861` and `fixed4=0.07996012542371823`, adaptive mean absolute delta to fixed4 `0.015857634309498155`, adaptive max absolute delta to fixed4 `0.03813519278690912`, and policy total truncation errors `adaptive2_4=0.09068182502839886` versus `fixed4=0.00003207982369080373`. This is important negative tensor evidence: the one-cycle low-cap adaptive stability does not persist at two cycles, so adaptive D=2/4 remains a bounded first-rung route rather than convergence evidence.
30. **L64 fixed higher-cap pilot:** `sim_two_root_constraint_l64_fixed_high_cap_pilot_probe.py` compares fixed D=4 against fixed D=6 on a bounded two-cycle L64 MPS surface for `plus_x` and `alternating_z`. It reports `l64_fixed_high_cap_status=bounded_l64_fixed_high_cap_pilot_complete`, `trajectory_count=4`, `completed_trajectories=4`, `stages_completed=64`, elapsed `50.875943183898926`, policy mean center-pair `I(A:B)` values `fixed4=0.09834903841001183` and `fixed6=0.0894102987840435`, fixed6 mean absolute delta to fixed4 `0.01208985544576776`, max delta `0.021028595071736086`, and total truncation `fixed4=1.1031649376108431e-05` versus `fixed6=4.807890724381438e-06`. The per-row result is mixed: `alternating_z` improves strongly at D6, while `plus_x` has higher truncation at D6. This means cap-only scaling is informative but not enough for convergence; local Krylov or vectorized doubled-MPS Lindblad remains the cleaner next algorithmic route.
31. **L64 doubled-MPS deterministic Lindblad pilot:** `sim_two_root_constraint_l64_doubled_mps_lindblad_pilot_probe.py` implements the first Liouville-space doubled-MPS route: density operators are represented as physical-dimension-4 MPS tensors, exact local terrain Lindblad channels are applied with `torch.linalg.matrix_exp`, and two-site unitary dynamics is applied as a Liouville superoperator. It reports `l64_doubled_mps_status=bounded_l64_doubled_mps_lindblad_pilot_complete`, `trajectory_count=8`, `completed_trajectories=8`, `stages_completed=128`, elapsed `4.0022101402282715`, `max_global_trace_error=6.662783593823664e-16`, `min_pair_eigenvalue=0.0030924883817899235`, and dynamic-minus-no-entangler center-pair `I(A:B)` with mean `4.722349336211407e-06` and max `9.436902989712337e-06`. This is a real deterministic tensor-algorithm advance beyond stochastic trajectory/cap probes, but the Phi0 separation is tiny and remains nonpromotional.
32. **PEPS/PEPS3D stage-loop depth inventory:** `sim_two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe.py` implements the current per-engine-stage path: all 16 stage placements (`2 sheets x 2 loops x 4 stage slots`) and the four L/R inner/outer loop composites run one by one on PyTorch-native PEPS `2x4` and PEPS3D `2x2x2` substrates. It reports `completion_status=peps_peps3d_stage_loop_depth_inventory_complete`, `stage_row_count=64`, `loop_row_count=16`, `unique_stage_placements=16`, `unique_loop_ids=4`, max norm errors below `4.440892098500626e-16`, max loop edge-MI gap `0.7504982891524838`, and `z3_final_manifold_admission_allowed=false`. This is a useful depth inventory for deciding where the engine stack has substrate response, but it is pure-state no-jump simple-update evidence rather than deterministic MPDO Lindblad, full PEPS/PEPS3D convergence, scale-level basin admission, or final manifold admission.

### Latest Side-Quest Evidence To Route, Not Promote Blindly

`system_v5/grok_sim/results/iter_184_basin_clustering_threshold_sweep_results.json` through `iter_194_peps_engine_2x4_results.json` are now routed by `sim_two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe.py`.

Routed findings:

- schedule pseudo-basin counts are threshold-sensitive, so basin-count claims need epsilon sweeps and controls;
- random CPTP controls show basin count alone is generic, while coplanarity/memory-horizon claims require explicit random-channel baselines;
- Euler Lindblad stepping and log-only scale-up attempts cannot support CPTP claims;
- proper 8-terrain laws and the two-engine FIFO classifier idea are reproduction targets only;
- MPS/PEPS sidequest attempts are weaker than the current formal MPS/PEPS/PEPS3D first-rung receipts and do not change admission status.

`system_v5/grok_sim/results/iter_195_engine_deep_spectral_basin_results.json` is useful but still `claim_ceiling: side_quest_only`.

Reported side-quest result:

- single exact-CPTP engine has one fixed-point eigenvalue at 1;
- slow real decay eigenvalue magnitude about `0.125`;
- fast conjugate modes magnitude about `0.0078`;
- spectral gap about `0.87`;
- CPTP checked at Choi level;
- Type-1/Type-2 engine superoperators do not commute;
- Trotter error versus all-Lindblads-at-once is substantial;
- 200/200 random pure states converge to the same fixed point in about 2-4 cycles;
- the two-engine schedule memory horizon is explained by geometric decay of the slow mode.

This has now become a green formal reproduction target. It is still not an immediate admission claim.

## Core Interpretation To Preserve

1. **Terrains are placements.** `Se`, `Ne`, `Ni`, `Si` are topology-family density-law placements on Weyl-sheet density states. They are not primitive topology classes by themselves.
2. **Engines are composite pseudo-attractor objects.** An engine is an ordered inner/outer composition of terrain-stage CPTP laws.
3. **A fixed single engine is monostable.** The newest spectral evidence explains why: one primitive fixed point and a strong spectral gap.
4. **Schedule pseudo-basins live above the engine.** The measured four-class structure is schedule/history memory, not multiple basins of one fixed engine.
5. **True basin admission needs one generated runtime map.** It can be adaptive, state-dependent, coupled, nonlinear, or piecewise, but it cannot be a family of different fixed schedules.
6. **Constraint layers are the ratchet.** F01/N01 start the admissibility surface; terrain, engine, schedule, bridge, tensor runtime, and Phi0 add cumulative structure.
7. **Axis0 entropy is layer-indexed.** `L2` chart sign / torus-seat entropy gradient is not the same object as `L4` `Phi0(rho_AB)`. The current L4 Phi0 family is nonpromotional under controls. The first `L7` schedule-history `Xi` scout is executable but nonseparating under controls, and the follow-up theta-base/adversarial-control scout shows the L7 signal is nonzero without the floor but still weaker than a `time_reversed` control. L8 shell-weighted `I_c` is therefore blocked as bridge evidence until `Xi` is redesigned or L7 survives stronger controls.
8. **Phi0 can fail.** A killed or nonseparating Phi0 is a valid result. Do not force a bridge claim.

## Target Runtime Stack

The runtime must represent and emit this stack:

1. F01 finite-carrier predicate.
2. N01 noncommuting-operator predicate.
3. Admissibility set `C`.
4. Constraint manifold `M(C)` as carrier/relation/state tuples.
5. Weyl-sheet density carriers.
6. Terrain placement laws: `Se`, `Ne`, `Ni`, `Si`.
7. Terrain-stage site slots.
8. Type-1 and Type-2 engine maps.
9. Schedule words over engine maps.
10. Adaptive or generated piecewise runtime state.
11. Paired/coupled E=8 + E=8 engine substrate.
12. Tensor-network lift.
13. Bridge `Xi`.
14. Cut-state `rho_AB`.
15. Phi0 correlational entropy family.
16. Admission classification.

Use `E`, `L`, `R`, `q`, and `N` carefully:

- `E` = engine-stage or terrain-placement substrate count.
- `L` = tensor-network site count.
- `R` = schedule repeat count.
- `q` = Pauli substrate qubit count.
- `N` = selected operator count or schedule length when explicitly named.

Do not conflate these in result JSONs.

## Workstream 0: Re-anchor And Route Latest Side-Quest Evidence

Goal: bring iter_195 into formal scope correctly.

Current status: **complete as formal reproduction evidence** via `sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py`.

Build:

- `sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py`;
- exact torch reproduction of the single-engine channel spectrum;
- Choi CPTP check;
- commutator norm between Type-1 and Type-2 channels;
- Trotter-vs-sequential order comparison;
- convergence-time basin map;
- memory-kernel explanation from slow eigenmode magnitude.

Controls:

- all-Lindblads-at-once channel;
- reversed stage order;
- shuffled terrain order;
- Type-1 only / Type-2 only;
- tau variations around the reported point;
- numerical tolerance sweep for memory-horizon classification.

Done when:

- the formal receipt either reproduces the side-quest spectral numbers or names the exact mismatch;
- the result stays sidequest-derived/formal-reproduction scoped unless it passes the scout contract;
- README and handoff are updated.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json`
- summary: `formal_reproduction_status=reproduced`, `single_engine_status=primitive_monostable_cptp_channel`, slow mode `0.12533379663284297`, spectral gap `0.8746662033671571`, commutator norm `0.47665693288252564`, Trotter error `0.18526280348505894`.

## Workstream 1: Spectral Manifold Map

Goal: turn "one engine has slow mode 0.125" into a function on the parameter/manifold surface.

Current status: **complete as bounded spectral-map evidence** via `sim_two_root_constraint_engine_spectral_manifold_phase_map_probe.py`.

Build sweeps over:

- tau;
- terrain rates;
- Hamiltonian direction;
- Hamiltonian magnitude;
- Type-1/Type-2 sign;
- stage order;
- inner/outer realization.

Required readouts:

- eigenvalue magnitudes and phases;
- spectral gap;
- primitive/nonprimitive flag;
- fixed-point Bloch vector;
- convergence half-life;
- memory-horizon estimate as a function of threshold;
- alignment of fixed point and slow mode with Hamiltonian direction;
- relation between slow-mode residue and schedule class count.

Done when:

- a spectral phase table exists;
- the schedule-memory phase map can be explained or refuted by channel spectrum;
- the result names where schedule memory should be last-1, last-2, higher, collapsed, or non-suffix.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json`
- summary: 1,080 rows, anchor slow mode `0.12533379663284297`, anchor spectral gap `0.8746662033671571`, slow-mode range `[0.003989385123239639, 0.7672214262697518]`, spectral-gap range `[0.23277857373024824, 0.9960106148767603]`, primitive statuses `fast_mixing=120`, `slow_mode_memory=462`, `long_memory=498`, and order-channel norms `canonical_minus_reversed=0.22408826165977588`, `canonical_minus_all_at_once=0.18526280348505894`.

## Workstream 2: Terrain Contribution / Stage Decomposition

Goal: identify which terrain placements create or destroy the slow memory mode.

Current status: **complete as bounded terrain/stage contribution evidence** via `sim_two_root_constraint_terrain_stage_spectral_contribution_probe.py`.

Build:

- remove-one-stage ablations;
- duplicate-one-stage ablations;
- reorder inner and outer stages;
- compare sequential Trotter channel against all-Lindblads-at-once channel;
- per-stage contribution to fixed point and slow eigenmode;
- KAK/chirality-admissible operator-slot checks when using two-qubit gates.

Controls:

- identity terrain replacement;
- matched total Lindbladian norm;
- random terrain order with same rates;
- Hermitian versus non-Hermitian Lindblad class split.

Done when:

- terrain placement contribution is quantified;
- "engine order is load-bearing" is either supported by controls or killed;
- the result explains which terrain sub-pseudo-attractors feed the engine pseudo-attractor.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_terrain_stage_spectral_contribution_probe_results.json`
- summary: baseline slow mode `0.12533379663284297`, baseline spectral gap `0.8746662033671571`, strongest removal suppressor `remove_all_Ni` with delta `0.11704323484005719`, strongest duplication damping `duplicate_all_Ni` with delta `-0.058585148208287516`, strongest single drop `drop_pos_4_Se`, strongest single duplicate `duplicate_pos_6_Ni`, reversed-order channel delta `0.22408826165977588`, and all-at-once channel delta `0.18526280348505894`.

## Workstream 3: Bridge `Xi -> rho_AB -> Phi0` Repair Or Falsification

Goal: decide whether the bridge can separate from controls.

Current state:

- product-substrate bridge is killed/near-zero for mutual-information separation;
- MPS bridge mutual information is nonzero but not control-separated;
- late Grok 196-203 adds useful sidequest targets for slow-mode projection, n-hat alignment, extreme tau scales, and multisite spectral scaling, but direct promotion is blocked because the sources are NumPy/SciPy;
- slow-mode/n-hat/terrain-informed bridge repair has been tested and remains open/nonseparating because terrain-erased control beats the canonical bridge;
- coupled-E16 stress controls demoted the weak bridge to open/nonrobust internal controls;
- response-gradient repair after stress also remains open/nonrobust because terrain-erased and weak-coupling controls dominate the response/gradient;
- therefore the current Phi0 bridge family is open/nonrobust, not admitted.

Build:

- bridge maps that use schedule history, slow spectral mode, terrain-stage identity, and paired engine state;
- bridge maps that project or erase the slow Pauli/eigenvector component and Hamiltonian-direction/n-hat component identified by late sidequest routing;
- `rho_AB` construction from actual runtime histories, not metadata only;
- Phi0 family readout: `I_c(A->B)`, `S(A|B)`, `I(A:B)`;
- shell/weighted cut variants when justified by the atlas;
- bridge disabled after warmup;
- bridge using last-1 versus last-2 memory states.

Controls:

- zero bridge;
- shuffled bridge;
- type-swap bridge;
- random matched-norm bridge;
- history-erased bridge;
- slow-mode-projection-erased bridge;
- local-only bridge;
- product-state bridge.

Admission rule:

- canonical bridge must be nonzero and separated from controls by a named margin;
- if controls match it, status remains `open_nonseparating` or killed;
- do not promote nonzero MI by itself.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json`
- summary: `bridge_status=open_nonzero_not_control_separated`, canonical `I(A:B)=0.039914842216213775`, max control `terrain_erased_bridge_control=0.053958495023197106`, canonical-minus-max-control `-0.014043652806983331`, slow-mode alignment with n-hat `0.9993292407173685`, and `final_manifold_admission_allowed=false`.
- `system_v5/ops/formal_scouts/results/two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json`
- summary: `repair_status=open_nonrobust_response_controls`, canonical mean `I(A:B)=0.09083182167095172`, canonical mean no-coupling delta `0.05526207410925876`, max comparable delta `terrain_erased=0.1038555286726403`, max comparable absolute gradient `terrain_erased=1.2996814412379643`, max any absolute gradient `weak_coupling=4.729915700344511`, `repair_rescued=false`, and `final_manifold_admission_allowed=false`.

## Workstream 4: Full Coupled E=16 Runtime

Goal: move beyond product-substrate bridge metadata.

Build:

- two E=8 engines as an E=16 substrate;
- cross-engine coupling operator or schedule-dependent bridge;
- actual coupled dynamics, not paired post-hoc readout only;
- Type-1/Type-2 paired schedules;
- local and cross-engine observables;
- `rho_AB` extraction over meaningful cuts.

Acceptable first rungs:

- dense tiny-control only when state size is explicit and bounded;
- MPS paired-engine trajectory;
- vectorized doubled-MPS if feasible;
- local Krylov/TEBD route if MPS density growth blocks.

Done when:

- one coupled E=16 mechanism runs with controls, or a precise blocker receipt names the algorithmic wall;
- product-substrate results are preserved as baseline, not promoted.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json`
- summary: `workstream_4_status=coupled_e16_runtime_built`, `bridge_status=rescued_control_separated`, canonical mean `I(A:B)=0.12573777715326687`, max control `type_swap_control=0.12471879666007199`, canonical-minus-max-control `0.0010189804931948765`, no-coupling delta `0.10988579660901507`, and `final_manifold_admission_allowed=false`.
- boundary: this is a bounded dense E=16 runtime first rung. It does not promote L=32/L=64 tensor scaling, PEPS/PEPS3D dynamics, final manifold admission, or scale-level real attractor-basin admission.

## Workstream 5: Tensor-Network Lindblad Dynamics

Goal: make tensor networks load-bearing for dynamics.

Already green:

- 1D MPS quantum-trajectory Lindblad through L=16;
- dense L=4 replay validation;
- bounded L=16 truncation and nontrivial bond growth.
- bounded low-bond L32 MPS trajectory surface at bond cap 4 across four initial families.
- bounded low-bond L64 MPS trajectory surface at bond cap 4 across four initial families.
- small-grid 2D PEPS-style dynamics with local terrain no-jump steps, nearest-neighbor SVD gate updates, exact contraction readouts, and controls.
- tiny-grid 3D PEPS-style dynamics with local terrain no-jump steps, x/y/z nearest-neighbor SVD gate updates, exact contraction readouts, and controls.

Still open:

- L=32 convergence/bond-scaling beyond the bounded low-bond D=4 receipt;
- L=64 convergence/bond-scaling beyond the bounded low-bond D=4 receipt;
- PEPS dynamics beyond the tiny 2x2 simple-update first rung;
- PEPS3D dynamics beyond the tiny 2x2x2 simple-update first rung;
- multi-trajectory statistics at scale;
- bridge-level Phi0 separation at scale; current coupled-E16 Phi0 status is open/nonrobust after stress controls.

Required next methods:

- improved MPS trajectory algorithm;
- vectorized doubled-MPS Lindblad;
- non-Hermitian TEBD with trajectory controls;
- local Krylov;
- adaptive bond cap with explicit truncation bias receipt;
- PEPS/PEPS3D dynamic gate after 1D path is stable.

Scale ladder:

1. L=4 exact dense replay.
2. L=8 MPS trajectory.
3. L=16 MPS target, already green.
4. L=32 bounded low-bond mitigation, complete as first rung.
5. L=64 bounded low-bond mitigation, complete as first rung.
6. PEPS small-grid dynamics, complete as tiny 2D first rung.
7. PEPS3D tiny-grid dynamics, complete as tiny 3D first rung.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json`
- summary: `l32_status=bounded_low_bond_l32_surface_complete`, `mitigation_route=bounded_low_bond_l32_surface`, `stages_completed=192`, `families_completed=4`, `max_bond=4`, `total_truncation_error=0.02360643923876433`, `max_family_truncation_error=0.018405225557571625`, and `final_manifold_admission_allowed=false`.
- boundary: this is bounded low-bond L32 evidence, not L64 evidence, not PEPS/PEPS3D dynamics, not scale-level basin admission, and not a final tensor convergence theorem.
- `system_v5/ops/formal_scouts/results/two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json`
- summary: `l64_status=bounded_low_bond_l64_first_rung_complete`, `mitigation_route=bounded_low_bond_l64_surface`, `stages_completed=96`, `families_completed=4`, `max_bond=4`, `total_truncation_error=9.417845500992903e-05`, `max_family_truncation_error=5.516561765594344e-05`, and `final_manifold_admission_allowed=false`.
- boundary: this is bounded low-bond L64 evidence, not full L64 convergence or bond-scaling evidence, not full PEPS/PEPS3D dynamics, not scale-level basin admission, and not final manifold admission.
- `system_v5/ops/formal_scouts/results/two_root_constraint_peps_small_grid_dynamics_probe_results.json`
- summary: `peps_status=small_grid_peps_dynamic_control_separated`, grid `[2, 2]`, bond cap `2`, cycles `2`, dynamic-minus-max-control MI by family including `plus_x=0.0013512574711469463`, max dynamic norm error `1.1102230246251565e-16`, max dynamic truncation diagnostic `3.8346987982482204`, and `final_manifold_admission_allowed=false`.
- boundary: this is a tiny 2D PEPS-style dynamics first rung, not PEPS3D evidence, not L64 evidence, not full PEPS convergence, not scale-level basin admission, and not final manifold admission.
- `system_v5/ops/formal_scouts/results/two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json`
- summary: `peps3d_status=tiny_peps3d_dynamic_control_separated`, grid `[2, 2, 2]`, bond cap `2`, cycles `1`, selected-edge dynamic-minus-max-control MI by family including `plus_x=0.001879041546241533`, edge-max dynamic-minus-max-control MI including `plus_x=1.3307868724585532`, max dynamic norm error `1.1102230246251565e-16`, max dynamic truncation diagnostic `8.671044423429251`, and `final_manifold_admission_allowed=false`.
- boundary: this is a tiny 3D PEPS-style dynamics first rung, not L64 evidence, not full PEPS3D convergence, not scale-level basin admission, and not final manifold admission.
- `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json`
- summary: `stress_status=open_nonrobust_internal_controls`, stress rows `6`, `min_canonical_minus_max_internal_control=-0.13199144731783669`, canonical MI range `[0.06353867860158008, 0.11896471552798837]`, tensor-carrier challenge max `peps3d_tiny_edge_max_delta_max=1.3307868724585532`, and `final_manifold_admission_allowed=false`.
- boundary: this is a Phi0 stress-control demotion receipt, not L64 evidence, not robust Phi0 closure, not scale-level basin admission, and not final manifold admission.
- `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json`
- summary: `trace_refresh_status=refreshed_after_phi0_stress_controls`, `phi0_current_status=open_nonrobust_internal_controls`, `manifold_admitted=false`, `final_goal_complete=false`, and `final_manifold_admission_allowed=false`.
- boundary: the full trace is current after stress controls, but final admission is still blocked.

Admission requires:

- state evolution, not construction-only carrier creation;
- norm/trace preservation;
- positivity or valid trajectory ensemble;
- bond dimension and truncation error;
- schedule/basin readouts;
- Phi0 readouts;
- controls and dense small-L comparison.

## Workstream 6: Constraint-Manifold Runtime Object

Goal: make the manifold a concrete object, not an explanation after the fact.

Represent:

- points as admissible carrier/relation/state tuples;
- edges as admissible transitions/stage maps;
- charts as layer-local coordinates/readouts;
- terrain placements as charted density-law placements;
- schedules as paths;
- spectral quantities as functions on the manifold;
- bridge `Xi` as a map from history/geometry to `rho_AB`;
- Phi0 as the correlational entropy functional;
- graveyard entries as failed-admission points with evidence.

Required outputs:

- JSON layer trace;
- graph/DAG of layers and dependencies;
- result status per layer;
- controls per bridge/basin claim;
- admission guard;
- exact blocker list.

Done when:

- a single command emits a full manifold trace from runtime receipts and current scout outputs;
- final status is either admitted or explicitly blocked with exact blockers.

Done receipt:

- `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json`
- summary: `trace_refresh_status=refreshed_with_coupled_e16_runtime`, `phi0_current_status=weak_coupled_e16_control_separation_bounded_first_rung`, status counts `green_runtime=8`, `bounded_bridge_candidate=1`, `open=3`, `open_nonseparating=2`, `pseudo_basin=1`, `weak_basin_candidate=1`, `killed=1`, `blocked=1`, and `final_goal_complete=false`.
- boundary: the refreshed trace upgrades Phi0 from nonseparating MPS/slow-mode bridge evidence to weak bounded coupled-E16 control separation, but final admission remains blocked by L32/L64 tensor scaling, PEPS/PEPS3D dynamics, and scale-level basin admission.

## Workstream 7: Attractor-Basin Admission

Goal: classify basin status without overclaim.

Classes:

- `pseudo_basin`: schedule family has distinct attractor classes.
- `weak_basin_candidate`: one generated runtime map has multiple stable states or cycles under bounded evidence.
- `real_basin`: basin partitions survive perturbation, controls, scale, and readout changes.
- `manifold_admitted_basin`: real basin plus bridge/Phi0 and tensor-network/manifold trace.
- `killed`: controls or asymptotic analysis refute the claim.
- `open_nonseparating`: signal exists but controls match it.

Admission tests:

- fixed-state or fixed-cycle evidence;
- fixed-observable evidence where relevant;
- generated-channel or generated-piecewise-map evidence;
- perturbation-volume or basin-boundary evidence;
- finite-time versus asymptotic separation;
- scale check;
- parameter robustness;
- negative controls;
- bridge/Phi0 readout.

Current status:

- fixed single engines are monostable;
- schedule classes are pseudo-basins;
- adaptive hysteresis is a bounded weak-basin candidate;
- MPS L=16 schedule readouts are green 1D evidence;
- Phi0 is weakly control-separated only in the bounded coupled-E16 first rung;
- MPS and slow-mode/terrain Phi0 bridges remain nonseparating controls to preserve in the trace;
- final manifold admission is blocked.

## Workstream 8: Tool Integration

Goal: every tool is load-bearing or explicitly unused.

Tool roles:

- PyTorch: primary nonclassical compute path.
- quimb/tensor network library: load-bearing state evolution, not construction-only.
- cotengra/opt_einsum: contraction planning only when contraction evidence is claimed.
- rustworkx/networkx: schedule/manifold graph and adjacency.
- z3/cvc5: admission and nonpromotion guards.
- sympy: exact symbolic identities only.
- clifford: Clifford/Pauli distinction only when active.
- geomstats: S2/S3/Bloch geometry metrics.
- GUDHI/TopoNetX/XGI: topology/persistence/hypergraph claims.
- LiRPA/e3nn/PyG: only with named bound/equivariance/GNN target.

No decorative imports count.

Every formal scout must include:

- `classification`;
- `claim_ceiling`;
- non-empty `TOOL_MANIFEST`;
- `TOOL_INTEGRATION_DEPTH`;
- result JSON under `system_v5/ops/formal_scouts/results/`;
- lint pass by `scripts/lint_sim_contract.py`.

## Recommended Execution Order

1. Formal reproduction of iter_195 spectral engine result. **Complete; preserve as anchor.**
2. Spectral phase map over engine/manifold parameters. **Complete; preserve as anchor.**
3. Terrain contribution and stage-order decomposition. **Complete; preserve as anchor.**
4. Late Grok 184-194 routing. **Complete; use only as controls/guardrails, not promotion evidence.**
5. Bridge Phi0 repair/falsification using spectral, terrain-stage, and MPS history features. **Complete as open/nonseparating falsifier.**
6. Coupled E=16 runtime beyond product substrate. **Complete as bounded dense E=16 first rung; the initial weak control separation is now superseded by stress-control demotion.**
7. Full manifold trace refresh using the new coupled E=16 receipt. **Complete but superseded by the post-stress trace; final admission still blocked.**
8. L=32 MPS algorithmic mitigation or precise blocked receipt. **Complete as bounded low-bond first rung; not full convergence.**
9. L=64 MPS algorithmic mitigation or precise blocked receipt. **Complete as bounded low-bond first rung; not full convergence.**
10. PEPS small-grid dynamics. **Complete as tiny 2D first rung; not final PEPS convergence.**
11. PEPS3D tiny-grid dynamics. **Complete as tiny 3D first rung; not final PEPS3D convergence.**
12. PEPS/PEPS3D stage-loop depth inventory. **Complete as 16-placement plus four-loop tiny-substrate inventory; not MPDO Lindblad or full PEPS/PEPS3D convergence.**
12. Coupled-E16 Phi0 stress controls. **Complete; Phi0 current status demoted to open/nonrobust internal controls.**
13. Phi0 response-gradient repair after stress. **Complete as open/nonrobust response-controls falsifier; current bridge family is not rescued.**
14. Full manifold trace refresh after Phi0 stress. **Complete; final admission still blocked.**
15. Late Grok 204-212 routing. **Complete; all nine sidequest sources are NumPy/SciPy-bound and nonpromotional, but they route implementable targets.**
16. Engine entropy-decay asymptotic and robustness. **Complete; exact first-cycle decay is rejected, asymptotic decay is supported, gamma_P trajectory is smooth/monotone, and small Hermitian perturbations keep the slow mode robust.**
17. L4 entropy-cell witness matrix. **Complete; required L4 bipartite entropy cells have numeric witnesses, but current Phi0 bridge remains open/nonrobust.**
18. Causal-irreversibility `Xi` bridge redesign. **Complete as open/nonseparating; the bridge is nonzero above no-coupling but still loses to random matched-norm controls and does not allow L8.**
19. L64 adaptive-vs-fixed bond-cap bias sweep. **Complete as bounded one-cycle cap-bias evidence; adaptive readouts are close to fixed caps, but this is not full L64 convergence.**
20. L64 two-cycle fixed/adaptive stability. **Complete; adaptive D=2/4 diverges from fixed D=4 at two cycles, so low-cap adaptive evidence is bounded and not convergence evidence.**
22. Basin admission receipt.
23. Tool/provider audit.
24. Final synthesis only if blockers are actually closed.

## Stop Conditions

Stop and write a blocked receipt if:

- L=32/L64 MPS hits bond saturation without a named alternative;
- PEPS/PEPS3D route only constructs carriers and does not run dynamics;
- Phi0 remains nonseparating against controls;
- adaptive/piecewise basins vanish under shuffled thresholds;
- tool integration becomes decorative;
- a scout needs broad NumPy in the nonclassical compute path;
- result JSON cannot support the claim being made.

## Success Condition

The full goal is complete only when the repo has:

- reusable QIT engine runtime;
- formal spectral engine explanation;
- full schedule/coupled-engine execution;
- tensor-network Lindblad dynamics at the target scale or exact blocked receipt;
- PEPS/PEPS3D dynamic evidence or exact blocked receipt;
- concrete constraint-manifold trace;
- admitted or killed attractor-basin criterion;
- `Xi -> rho_AB -> Phi0` receipt with control separation or honest kill;
- full tool-role receipt;
- no overclaim against controls.

If any of Phi0 separation, PEPS/PEPS3D dynamics, or scale-level basin admission remains open, the final synthesis must say `goal_complete=false`.

Current next pressure points after the L64 adaptive-bond batch, the L64 cap-bias sweep, the L64 two-cycle stability check, the L64 fixed D6 pilot, the L64 doubled-MPS deterministic pilot, the PEPS/PEPS3D 16-placement depth inventory, the late-Grok 204-212 audit, the L4 entropy-cell witness matrix, and the causal-irreversibility `Xi` redesign are: either convert the PEPS/PEPS3D depth inventory into deterministic MPDO Lindblad dynamics, invent a still-different `Xi -> rho_AB -> Phi0` mechanism that survives random/time-reversed/terrain-erased controls, stress the doubled-MPS route against longer horizons/bond caps/trajectory ensembles, add local Krylov batching, or move to a scale-level basin admission falsifier. A broader fixed-cap surface (`D6` all families/seeds or bounded `D8`) is allowed only as diagnostic cap-scaling evidence because the D6 pilot is mixed. Do not revisit final admission until robust Phi0 and full tensor evidence exist.

Late-Grok 204-212 current evidence:

- routing receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_204_212_engine_axis0_sidequest_routing_probe_results.json`;
- direct formal promotion: blocked; all nine sidequest sources use NumPy or SciPy;
- strongest routed target: `sim_two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe.py`;
- second routed target: `sim_two_root_constraint_l4_entropy_cell_witness_matrix_probe.py`;
- implemented strongest target receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe_results.json`;
- result: `engine_entropy_decay_status=asymptotic_not_exact_first_cycle`, `lambda_1_squared=0.01570856057840284`, `mean_first_cycle_ratio=0.009148593734967559`, `mean_late_cycle_ratio=0.015709103592017444`, `gamma_trajectory_status=smooth_monotone`, `small_delta_slow_mode_status=robust_bounded`, `final_manifold_admission_allowed=false`;
- sidequest correction: the iter_212 random Bloch vector is slightly outside the Bloch ball and the random coherent perturbation is non-Hermitian, so the formal receipt normalizes the state and replaces the perturbation with a Hermitian Pauli combination.

L4 entropy-cell current evidence:

- receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_l4_entropy_cell_witness_matrix_probe_results.json`;
- result: `l4_entropy_cell_status=numeric_witness_matrix_complete`, required cells `I_A_colon_B`, `S_A_given_B`, `I_c_A_to_B`, `negativity`, `log_negativity`, and `concurrence` all witnessed;
- signed cells have both signs, stage-local entanglement is positive, whole-engine entanglement is not promotional, and `final_manifold_admission_allowed=false`;
- strongest stage-local values include mutual information max `0.930336419473681`, coherent information range `[-0.24499372561443045, 0.2371892389137356]`, negativity max `0.36802501789644065`, log-negativity max `0.5516124382841364`, and concurrence max `0.7784279261753763`;
- boundary: this proves L4 entropy forms are executable and nontrivial; it does not rescue the current `Xi -> rho_AB -> Phi0` bridge, which remains open/nonrobust under controls.

Causal-irreversibility `Xi` current evidence:

- receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe_results.json`;
- source: `system_v5/ops/formal_scouts/sim_two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe.py`;
- result: `xi_causal_irreversibility_status=open_nonzero_not_control_separated`, best metric `I_c_A_to_B`, `canonical_nonzero_any_metric=true`, and `canonical_control_separated_any_metric=false`;
- canonical beats no-coupling only weakly: `I(A:B)` delta `0.00031091535856928954`, coherent-information delta `0.0002121528777928594`, and directional-coherent delta `0.00011339039701643386`;
- random matched-norm remains stronger on the main bridge readouts: `I(A:B)` canonical-minus-max-control `-0.00043089567825572674`, coherent-information canonical-minus-max-control `-0.00014006231835850258`;
- boundary: this is a genuine redesigned `Xi` attempt because the bridge is derived from runtime channel irreversibility and fixed-point response, but it still does not survive adversarial controls, does not allow L8 shell-weighted evidence, and keeps final manifold admission blocked.

L64 cap-bias current evidence:

- receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_l64_adaptive_bond_bias_sweep_probe_results.json`;
- source: `system_v5/ops/formal_scouts/sim_two_root_constraint_l64_adaptive_bond_bias_sweep_probe.py`;
- result: `l64_bias_sweep_status=bounded_l64_adaptive_bias_sweep_complete`, `trajectory_count=24`, `completed_trajectories=24`, `stages_completed=192`, and `final_manifold_admission_allowed=false`;
- policy mean center-pair `I(A:B)`: adaptive D=2/4 `0.07515230420336619`, fixed D=2 `0.07515307590557144`, fixed D=4 `0.07534442198306783`;
- adaptive-vs-fixed deltas are small on this one-cycle surface: mean absolute delta to fixed4 `0.00020854331586046506`, max absolute delta to fixed4 `0.000657306790395995`, mean absolute delta to fixed2 `0.00005667585084512261`, max absolute delta to fixed2 `0.0002297902122014861`;
- truncation behaves as expected: adaptive total `1.4273902332923543e-05`, fixed D=2 total `4.169107486913291e-05`, fixed D=4 total `4.139166310236371e-09`;
- boundary: this strengthens the L64 tensor-runtime path by measuring cap-policy bias, but it is still one-cycle 1D MPS evidence and does not prove full L64 convergence, PEPS/PEPS3D closure, robust Phi0, or real basin admission.

L64 two-cycle stability current evidence:

- receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe_results.json`;
- source: `system_v5/ops/formal_scouts/sim_two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe.py`;
- result: `l64_two_cycle_status=bounded_l64_two_cycle_stability_complete`, `trajectory_count=16`, `completed_trajectories=16`, `stages_completed=256`, and `final_manifold_admission_allowed=false`;
- adaptive D=2/4 is not stable against fixed D=4 at two cycles: policy mean center-pair `I(A:B)` values are adaptive `0.06466151342308861` versus fixed4 `0.07996012542371823`, with adaptive mean absolute delta `0.015857634309498155` and max absolute delta `0.03813519278690912`;
- truncation is the decisive signal: adaptive D=2/4 total truncation error `0.09068182502839886` versus fixed D=4 total truncation error `0.00003207982369080373`;
- boundary: this is useful negative tensor evidence. It keeps the L64 route alive, but it blocks using low-cap adaptive D=2/4 as convergence evidence. Further L64 progress needs higher fixed caps, local Krylov, vectorized doubled-MPS Lindblad, or another algorithmic route.

L64 fixed higher-cap pilot current evidence:

- receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json`;
- source: `system_v5/ops/formal_scouts/sim_two_root_constraint_l64_fixed_high_cap_pilot_probe.py`;
- result: `l64_fixed_high_cap_status=bounded_l64_fixed_high_cap_pilot_complete`, `trajectory_count=4`, `completed_trajectories=4`, `stages_completed=64`, elapsed `50.875943183898926`, and `final_manifold_admission_allowed=false`;
- fixed D=6 changes the center-pair readout relative to fixed D=4: policy mean `I(A:B)` is fixed4 `0.09834903841001183` versus fixed6 `0.0894102987840435`; fixed6 mean absolute delta to fixed4 is `0.01208985544576776` and max delta is `0.021028595071736086`;
- fixed D=6 lowers aggregate truncation (`4.807890724381438e-06` versus fixed4 `1.1031649376108431e-05`) but not uniformly: `alternating_z` improves strongly at D6 while `plus_x` has higher truncation at D6;
- boundary: this is a bounded two-family D6 pilot, not full L64 convergence or bond-scaling closure. It argues against treating cap-only scaling as solved and keeps local Krylov or vectorized doubled-MPS Lindblad as the cleaner next tensor route.

L64 doubled-MPS deterministic Lindblad current evidence:

- receipt: `system_v5/ops/formal_scouts/results/two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json`;
- source: `system_v5/ops/formal_scouts/sim_two_root_constraint_l64_doubled_mps_lindblad_pilot_probe.py`;
- result: `l64_doubled_mps_status=bounded_l64_doubled_mps_lindblad_pilot_complete`, `trajectory_count=8`, `completed_trajectories=8`, `stages_completed=128`, elapsed `4.0022101402282715`, and `final_manifold_admission_allowed=false`;
- tensor route: density operators are represented as Liouville-space MPS tensors with physical dimension 4, exact local terrain Lindblad channels are applied by `torch.linalg.matrix_exp`, and the nearest-neighbor unitary is lifted to a two-site Liouville superoperator;
- physicality checks: `max_global_trace_error=6.662783593823664e-16`, `min_pair_eigenvalue=0.0030924883817899235`, and local pair Hermiticity stays inside tolerance;
- readout: dynamic-minus-no-entangler center-pair `I(A:B)` is positive but tiny, with mean `4.722349336211407e-06` and max `9.436902989712337e-06`;
- boundary: this advances the tensor algorithm beyond stochastic trajectory/cap probes, but it is still a bounded first rung. It does not prove full L64 convergence, robust Phi0, PEPS/PEPS3D closure, or real scale-level basin admission.
