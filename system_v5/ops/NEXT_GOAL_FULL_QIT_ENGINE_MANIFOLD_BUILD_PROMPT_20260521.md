# Next Goal Prompt: Full QIT Engine / Constraint Manifold Build

**Updated:** 2026-05-21
**Status:** RETIRED - audit freeze as of 2026-05-22T05:00:34Z
**Plan:** `system_v5/ops/QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md`

## 2026-05-22 Retirement Notice

Do not use this as the next goal prompt.

The full engine/manifold build is halted by `system_v5/ops/QIT_ENGINE_MANIFOLD_AUDIT_FREEZE_20260522.md`. The next admissible goal is not to continue PEPS/PEPS3D, Phi0, or basin construction. The next admissible goal is to audit and repair the source-to-runtime mapping for axes/operators/terrains, then quarantine or reclassify all dependent results.

## Paste-Ready Goal

Continue in `/Users/joshuaeisenhart/Desktop/Codex Ratchet`.

Primary goal: build the full QIT engine / geometric constraint manifold runtime described in `system_v5/ops/QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md`.

This is not a wiki-routing task and not a prose-synthesis task. Build and test the engines, manifold runtime, tensor-network dynamics, bridge/Phi0 readout, and attractor-basin admission path. The previous goal was supposed to move toward this, but it did not finish the full target. Preserve what it completed and attack the remaining blockers directly.

Read first:

- `AGENTS.md`
- `system_v5/ops/QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md`
- `system_v5/ops/NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md`
- `.lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md`
- `system_v5/ops/formal_scouts/README.md`
- `system_v5/ops/formal_scouts/qit_engine_runtime.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_schedule_memory_phase_map_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_adaptive_engine_switching_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_phi0_bridge_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_tensor_network_lindblad_runtime_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_terrain_stage_spectral_contribution_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_peps_small_grid_dynamics_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json`
- `system_v5/ops/formal_scouts/results/two_root_constraint_l7_xi_history_phi0_bridge_probe_results.json`
- `system_v5/grok_sim/results/iter_195_engine_deep_spectral_basin_results.json`

Current truth:

- Workstream A is complete: `qit_engine_runtime.py` centralizes the exact torch terrain/engine/schedule runtime.
- Workstream B is complete: schedule-memory phase map covers tau, dissipator profile, Hamiltonian direction, and Hamiltonian magnitude.
- Workstream C is complete at bounded single-qubit scope: `schedule_memory_hysteresis_z` is a weak-basin candidate on augmented `(rho, previous-engine-token)` state.
- Workstream D product-substrate bridge is killed/near-zero for Phi0 separation.
- Workstream E is green at 1D MPS trajectory L=16 with dense L=4 replay validation.
- MPS bridge-level Phi0 is nonzero but not control-separated: canonical mean `I(A:B)=0.0945`, shuffled `0.0867`, type-swap `0.0945`, random matched-norm `0.0447`, zero `0.0196`.
- Full trace is green as a trace but blocked as admission: `final_goal_complete=false`, `phi0_separates=false`, `peps_extension=false`, `manifold_admitted=false`.
- Latest grok sidequest iter_195 has now been formally reproduced by `sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py`: one fixed eigenvalue, slow mode `|lambda|=0.12533379663284297`, spectral gap `0.8746662033671571`, Choi CPTP, noncommuting T1/T2 engines with commutator norm `0.47665693288252564`, Trotter error `0.18526280348505894`, and monostable convergence from 200/200 random pure states. It is formal reproduction evidence, not final admission.
- Spectral manifold phase map is complete as bounded evidence: 1,080 rows, slow-mode range `[0.003989385123239639, 0.7672214262697518]`, spectral-gap range `[0.23277857373024824, 0.9960106148767603]`, and order-channel norms showing canonical order differs from reversed/all-at-once.
- Terrain/stage spectral contribution is complete as bounded evidence: all four terrain families suppress the slow memory mode in the canonical engine, Ni is strongest by removal and duplication tests, stage placement matters, reversed-order channel delta is `0.22408826165977588`, and all-at-once channel delta is `0.18526280348505894`.
- Grok iter_184-194 has been routed, not promoted: every source is NumPy/SciPy/quimb or Euler/log-only boundary work. The batch helps only by adding threshold-sensitivity guards, random-CPTP coplanarity/memory controls, proper-terrain reproduction targets, and negative/superseded MPS/PEPS sidequest context.
- Grok iter_196-203 has been routed, not promoted: every source uses NumPy/SciPy, but the batch helps the next formal packet by naming slow-mode Pauli/eigenvector projection, Hamiltonian-direction/n-hat alignment, extreme tau critical scales, and multisite spectral scaling targets.
- Phi0 slow-mode/terrain bridge repair has been tested and remains open/nonseparating: canonical `I(A:B)=0.039914842216213775`, terrain-erased control `I(A:B)=0.053958495023197106`, canonical-minus-max-control `-0.014043652806983331`.
- Coupled E=16 runtime has been built as a bounded dense first rung: canonical mean `I(A:B)=0.12573777715326687`, max control `type_swap_control=0.12471879666007199`, canonical-minus-max-control `0.0010189804931948765`, no-coupling delta `0.10988579660901507`, `bridge_status=rescued_control_separated`, and `final_manifold_admission_allowed=false`.
- Coupled-E16 Phi0 stress controls have now demoted that weak bridge: `stress_status=open_nonrobust_internal_controls`, `min_canonical_minus_max_internal_control=-0.13199144731783669`, canonical MI range `[0.06353867860158008, 0.11896471552798837]`, tensor-carrier challenge max `peps3d_tiny_edge_max_delta_max=1.3307868724585532`, and `final_manifold_admission_allowed=false`.
- Phi0 response-gradient repair after stress has been tested and does not rescue the current bridge family: `repair_status=open_nonrobust_response_controls`, canonical mean `I(A:B)=0.09083182167095172`, canonical minimum no-coupling delta `0.013053955645177695`, canonical mean no-coupling delta `0.05526207410925876`, canonical mean absolute gradient `0.7330243954009311`, max comparable delta `terrain_erased=0.1038555286726403`, max comparable absolute gradient `terrain_erased=1.2996814412379643`, max any absolute gradient `weak_coupling=4.729915700344511`, `tensor_carrier_challenge_passed=false`, and `final_manifold_admission_allowed=false`.
- Full manifold trace has been refreshed after Phi0 stress controls: `trace_refresh_status=refreshed_after_phi0_stress_controls`, `phi0_current_status=open_nonrobust_internal_controls`, `manifold_admitted=false`, `final_goal_complete=false`.
- Axis0 layered entropy-ratchet audit is green: `axis0_entropy_ratchet_status=layered_doctrine_executable`, `current_phi0_failure_reframed_as_layer_mismatch=true`, `recommended_next_bridge_target=L7_Xi_history_or_L8_shell_weighted_phi0`, and `final_manifold_admission_allowed=false`. Preserve the layer split: `L2` chart sign / torus-seat entropy gradient is not the same object as `L4` `Phi0(rho_AB)`; `L4` signed bipartite forms unlock `S(A|B)` and `I_c` but the currently tested L4 bridge family remains nonpromotional under controls; `L6` adds Hopf/Chern support; `L7` schedule-history and `L8` shell-weighted forms are the next real bridge targets. Grok, Gemini direct API, Sonnet high, and Opus high external audits all returned `support_with_caveats`; keep the caveat in force that this is routing evidence, not Axis0 closure.
- L7 schedule-history `Xi -> rho_AB -> Phi0` bridge has now been built and tested: `l7_xi_history_status=open_nonzero_not_control_separated`, canonical mean `I(A:B)=0.009135587590283257`, max control `random_matched_norm_control=0.011937687839140024`, canonical-minus-max-control `-0.002802100248856767`, canonical-minus-no-coupling `0.009135587590283302`, and `final_manifold_admission_allowed=false`. Grok, Gemini direct API, Sonnet high, and Opus audits all returned `support_with_caveats`. The audit changes the next bridge order: do an L7 theta-base ablation plus structured adversarial-control scout first; only proceed to L8 shell-weighted if L7 history terms survive that confound/control gate.
- L7 theta-base/adversarial-control scout has now been built and tested: `l7_theta_adversarial_status=open_nonzero_not_control_separated`, zero-base canonical `I(A:B)=0.002676309726590367`, zero-base canonical-minus-no-coupling `0.002676309726590411`, zero-base max control `time_reversed` with `I(A:B)=0.004576765529614972`, zero-base canonical-minus-max-control `-0.0019004558030246048`, `floor_carries_signal=false`, `l8_shell_weighted_allowed_next=false`, and `final_manifold_admission_allowed=false`. This confirms the L7 signal is not just the unconditional floor, but it still does not separate from controls; do not proceed to L8 shell-weighted as bridge evidence without redesigning `Xi` or producing a new L7 family that survives controls.
- L32 has a bounded low-bond MPS mitigation receipt: `l32_status=bounded_low_bond_l32_surface_complete`, bond cap `4`, all four initial families complete, total truncation `0.02360643923876433`, max family truncation `0.018405225557571625`, and `final_manifold_admission_allowed=false`. This is not L64, PEPS/PEPS3D, full tensor convergence, or scale-level basin admission.
- L64 has a bounded low-bond MPS mitigation receipt: `l64_status=bounded_low_bond_l64_first_rung_complete`, bond cap `4`, all four initial families complete, 96 stages, elapsed `73.41843509674072s`, total truncation `9.417845500992903e-05`, max family truncation `5.516561765594344e-05`, and `final_manifold_admission_allowed=false`. This is not full L64 convergence, full tensor convergence, scale-level basin admission, or final manifold admission.
- L64 adaptive-bond trajectory batching has now been built and tested: `l64_adaptive_status=bounded_adaptive_l64_batch_complete`, `trajectory_count=8`, `completed_trajectories=8`, `stages_completed=64`, `cap_values_seen=[2,4]`, `cap_increase_count=2`, `cap_decrease_count=2`, `max_bond_observed=4`, `total_truncation_error=1.4273902332923543e-05`, `norm_error=1.7763568394002505e-15`, family mean center-pair `I(A:B)` values including `plus_x=0.2920463982362539`, and `final_manifold_admission_allowed=false`. This is stronger L64 tensor-runtime evidence than the fixed D=4 first rung, but it is still not full L64 convergence, PEPS/PEPS3D closure, robust Phi0, or scale-level basin admission.
- Grok iter_204-212 has been routed and partially formalized. The routing receipt `two_root_constraint_late_grok_204_212_engine_axis0_sidequest_routing_probe_results.json` has `all_pass=true` and blocks direct promotion because all nine sidequest sources use NumPy or SciPy. It names the strongest next packet as `sim_two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe.py` and the second as `sim_two_root_constraint_l4_entropy_cell_witness_matrix_probe.py`.
- The strongest iter_204-212 target is now implemented formally: `two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe_results.json` has `all_pass=true`, `engine_entropy_decay_status=asymptotic_not_exact_first_cycle`, `lambda_1_squared=0.01570856057840284`, `mean_first_cycle_ratio=0.009148593734967559`, `mean_late_cycle_ratio=0.015709103592017444`, `gamma_trajectory_status=smooth_monotone`, `small_delta_slow_mode_status=robust_bounded`, and `final_manifold_admission_allowed=false`. Preserve the corrected language: entropy decay approaches `|lambda_1|^2` only asymptotically after a transient; it is not exact from the first cycle. Also preserve the input correction: Grok iter_212's random Bloch vector is slightly outside the Bloch ball and its random coherent perturbation is non-Hermitian, so the formal receipt uses a valid random pure state and Hermitian perturbation.
- The second iter_204-212 target is now implemented formally: `two_root_constraint_l4_entropy_cell_witness_matrix_probe_results.json` has `all_pass=true`, `l4_entropy_cell_status=numeric_witness_matrix_complete`, required cells `I_A_colon_B`, `S_A_given_B`, `I_c_A_to_B`, `negativity`, `log_negativity`, and `concurrence` all witnessed, `signed_cells_have_both_signs=true`, `stage_local_entanglement_positive=true`, `whole_engine_entanglement_promotional=false`, and `final_manifold_admission_allowed=false`. Preserve the boundary: L4 cells are executable/nontrivial, but this does not rescue the current Phi0 bridge.
- A first genuinely redesigned `Xi` bridge has now been tested: `two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe_results.json` has `all_pass=true` and `xi_causal_irreversibility_status=open_nonzero_not_control_separated`. The bridge Hamiltonian is derived from schedule-channel forward/reverse asymmetry, fixed-point Bloch response, and channel noncommutation rather than the previous hand-shaped L7 history scalar. It creates weak nonzero response over no-coupling (`I(A:B)` delta `0.00031091535856928954`, coherent-information delta `0.0002121528777928594`) but still loses to controls (`I(A:B)` canonical-minus-max-control `-0.00043089567825572674`, coherent-information canonical-minus-max-control `-0.00014006231835850258`), sets `l8_shell_weighted_allowed_next=false`, and keeps `final_manifold_admission_allowed=false`. Preserve the boundary: this is real bridge redesign work, but it does not rescue Phi0 or unlock L8.
- L64 adaptive-vs-fixed cap bias has now been tested: `two_root_constraint_l64_adaptive_bond_bias_sweep_probe_results.json` has `all_pass=true`, `l64_bias_sweep_status=bounded_l64_adaptive_bias_sweep_complete`, `trajectory_count=24`, `completed_trajectories=24`, and `stages_completed=192`. Policy mean center-pair `I(A:B)` is adaptive D=2/4 `0.07515230420336619`, fixed D=2 `0.07515307590557144`, fixed D=4 `0.07534442198306783`; adaptive max absolute delta to fixed4 is `0.000657306790395995`. Truncation falls from fixed D=2 `4.169107486913291e-05` to adaptive `1.4273902332923543e-05` to fixed D=4 `4.139166310236371e-09`. Preserve the boundary: this measures one-cycle cap-policy bias and strengthens L64 tensor-runtime evidence, but it is not full L64 convergence, robust Phi0, PEPS/PEPS3D closure, or scale-level basin admission.
- L64 two-cycle fixed/adaptive stability has now been tested: `two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe_results.json` has `all_pass=true`, `l64_two_cycle_status=bounded_l64_two_cycle_stability_complete`, `trajectory_count=16`, `completed_trajectories=16`, and `stages_completed=256`. Adaptive D=2/4 no longer tracks fixed D=4 at two cycles: policy mean center-pair `I(A:B)` is adaptive `0.06466151342308861` versus fixed4 `0.07996012542371823`; adaptive max absolute delta to fixed4 is `0.03813519278690912`. Truncation is much larger for adaptive D=2/4 (`0.09068182502839886`) than fixed D=4 (`0.00003207982369080373`). Preserve the boundary: this is negative tensor evidence against treating low-cap adaptive D=2/4 as convergence evidence; further L64 progress needs higher fixed caps, local Krylov, vectorized doubled-MPS Lindblad, or another algorithmic route.
- L64 fixed higher-cap pilot has now been tested: `two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json` has `all_pass=true`, `l64_fixed_high_cap_status=bounded_l64_fixed_high_cap_pilot_complete`, `trajectory_count=4`, `completed_trajectories=4`, and `stages_completed=64`. Fixed D=6 lowers aggregate truncation versus D=4 (`4.807890724381438e-06` vs `1.1031649376108431e-05`) but not uniformly: `alternating_z` improves strongly, while `plus_x` has higher truncation at D6. The center-pair readout shifts: mean `I(A:B)` fixed4 `0.09834903841001183` vs fixed6 `0.0894102987840435`, max absolute delta `0.021028595071736086`. Preserve the boundary: this is a bounded two-family D6 pilot, not full L64 convergence, robust Phi0, PEPS/PEPS3D closure, or scale-level basin admission. It keeps cap-only scaling open/mixed and makes local Krylov or vectorized doubled-MPS Lindblad the cleaner next tensor route.
- L64 doubled-MPS deterministic Lindblad pilot has now been tested: `two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json` has `all_pass=true`, `l64_doubled_mps_status=bounded_l64_doubled_mps_lindblad_pilot_complete`, `trajectory_count=8`, `completed_trajectories=8`, and `stages_completed=128`. It represents density operators as Liouville-space MPS tensors with physical dimension 4, applies exact local terrain Lindblad channels by `torch.linalg.matrix_exp`, and applies two-site unitary dynamics as a Liouville superoperator at L32/L64. Physicality is clean (`max_global_trace_error=6.662783593823664e-16`, `min_pair_eigenvalue=0.0030924883817899235`), but dynamic-minus-no-entangler center-pair `I(A:B)` is tiny (`mean=4.722349336211407e-06`, `max=9.436902989712337e-06`). Preserve the boundary: this is a real deterministic tensor-algorithm first rung beyond stochastic trajectory/cap probes, but it is not full L64 convergence, robust Phi0, PEPS/PEPS3D closure, or scale-level basin admission.
- Small-grid PEPS dynamics has a tiny 2D first-rung receipt: `peps_status=small_grid_peps_dynamic_control_separated`, grid `[2, 2]`, bond cap `2`, cycles `2`, dynamic-minus-max-control MI includes `plus_x=0.0013512574711469463`, max dynamic norm error `1.1102230246251565e-16`, finite truncation diagnostic `3.8346987982482204`, and `final_manifold_admission_allowed=false`. This is not PEPS3D, full PEPS convergence, scale-level basin admission, or final manifold admission.
- Tiny PEPS3D dynamics has a tiny 3D first-rung receipt: `peps3d_status=tiny_peps3d_dynamic_control_separated`, grid `[2, 2, 2]`, bond cap `2`, cycles `1`, selected-edge dynamic-minus-max-control MI includes `plus_x=0.001879041546241533`, edge-max dynamic-minus-max-control MI includes `plus_x=1.3307868724585532`, max dynamic norm error `1.1102230246251565e-16`, finite truncation diagnostic `8.671044423429251`, and `final_manifold_admission_allowed=false`. This is not full PEPS3D convergence, scale-level basin admission, or final manifold admission.
- PEPS/PEPS3D stage-loop depth inventory has now been tested: `two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json` has `all_pass=true`, `completion_status=peps_peps3d_stage_loop_depth_inventory_complete`, `stage_row_count=64`, `loop_row_count=16`, `unique_stage_placements=16`, `unique_loop_ids=4`, PEPS grid `[2,4]`, PEPS3D grid `[2,2,2]`, max norm errors below `4.440892098500626e-16`, max loop edge-MI gap `0.7504982891524838`, and `z3_final_manifold_admission_allowed=false`. Preserve the boundary: this runs all 16 placements and the four L/R inner/outer loops one by one on tiny pure-state tensor substrates, but it is not MPDO Lindblad, full PEPS/PEPS3D convergence, L32/L64, scale-level basin admission, or final manifold admission.
- Fixed single engines are monostable. Do not keep looking for single-engine multi-basins unless adding a real new mechanism.
- Schedule-level classes are pseudo-basins, not real attractor basins by themselves.
- Terrains are topology-family placements realized as Weyl-sheet density laws, not primitive topologies.
- Engines are composite pseudo-attractor objects built from terrain-stage placements.
- Constraint layers are the ratchet/admission process.
- Full L64 convergence/bond-scaling beyond bounded fixed D=4/D=6 and doubled-MPS first-rung pilots, PEPS dynamics beyond the tiny 2x2 first rung, PEPS3D dynamics beyond the tiny 2x2x2 first rung, a genuinely different robust Phi0 bridge mechanism after the failed response-gradient repair, scale-level basin admission, and final manifold admission remain open.

Required next sequence:

1. **Preserve the iter_195 formal spectral reproduction anchor.**
   - Do not rerun sidequest-only variants unless testing a named mismatch.
   - Use `two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json` as the current formal anchor.

2. **Preserve spectral manifold map. COMPLETE.**
   - Sweep tau, rates, Hamiltonian direction/magnitude, Type-1/Type-2 sign, and stage order.
   - Record eigenvalues, spectral gap, fixed point, half-life, memory horizon, and alignment with Hamiltonian direction.

3. **Decompose terrain/stage contribution. COMPLETE.**
   - Remove, duplicate, and reorder terrain stages.
   - Compare sequential engine to all-Lindblads-at-once.
   - Identify which terrain placements create the slow memory mode.

4. **Repair or falsify bridge Phi0. COMPLETE AS OPEN/NONSEPARATING.**
   - Use schedule history, slow spectral mode, slow-mode Pauli/eigenvector projection, Hamiltonian-direction/n-hat alignment, terrain-stage identity, and MPS runtime states to construct `Xi -> rho_AB`.
   - Read `I_c(A->B)`, `S(A|B)`, and `I(A:B)`.
   - Require separation from zero, shuffled, type-swap, random matched-norm, history-erased, slow-mode-erased, n-hat-erased, terrain-erased, weak/strong coupling, response-gradient, and tensor-carrier controls.

5. **Build real coupled E=16 dynamics. COMPLETE AS BOUNDED FIRST RUNG.**
   - Move beyond product-substrate metadata.
   - Run paired E=8 + E=8 dynamics with a real coupling/bridge mechanism.
   - Extract `rho_AB` and Phi0 from runtime states.

6. **Refresh full manifold trace. COMPLETE.**
   - Incorporate the coupled E=16 runtime receipt.
   - Emit layers, terrain placements, engine maps, schedules, spectral functions, tensor runtime, bridge, `rho_AB`, Phi0, controls, and admission status.
   - Keep final admission blocked unless the blockers actually close.

7. **Advance tensor-network dynamics. COMPLETE AS L32 AND L64 LOW-BOND FIRST RUNGS.**
   - Preserve L=16 MPS as green baseline.
   - Address L=32 bond saturation with a named algorithm: improved MPS trajectories, vectorized doubled-MPS Lindblad, non-Hermitian TEBD, local Krylov, or explicit bounded-truncation receipt.
   - Preserve `sim_two_root_constraint_l64_tensor_blocker_or_mitigation_probe.py` as bounded low-bond L64 first-rung evidence.
   - Do not claim full L32/L64 convergence from bounded low-bond runs.

8. **Build PEPS/PEPS3D dynamics. TINY PEPS, TINY PEPS3D, AND STAGE/LOOP DEPTH INVENTORY COMPLETE.**
   - Construction-only PEPS/PEPS3D does not count.
   - Preserve `sim_two_root_constraint_peps_small_grid_dynamics_probe.py` as tiny 2D PEPS-style first-rung evidence.
   - Preserve `sim_two_root_constraint_peps3d_tiny_grid_dynamics_probe.py` as tiny 3D PEPS-style first-rung evidence.
   - Preserve `sim_two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe.py` as the tiny PEPS/PEPS3D 16-placement plus four-loop depth inventory.
   - Next PEPS/PEPS3D step should be deterministic MPDO Lindblad or a precise blocker, not another construction-only or pure no-jump inventory.
   - Record norm/trace, positivity or valid trajectory ensemble, truncation/contraction data, and Phi0 readouts.

9. **Classify basin status.**
   - Separate `pseudo_basin`, `weak_basin_candidate`, `real_basin`, `manifold_admitted_basin`, `killed`, and `open_nonseparating`.
   - Admit nothing without fixed-state/fixed-cycle evidence, controls, scale check, and bridge/Phi0 evidence.

Hard requirements:

- Use `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`.
- Keep nonclassical compute PyTorch-native.
- Add formal scouts under `system_v5/ops/formal_scouts/`.
- Write result JSONs under `system_v5/ops/formal_scouts/results/`.
- Include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, and `claim_ceiling`.
- Run `scripts/lint_sim_contract.py` for every new scout.
- Update `system_v5/ops/formal_scouts/README.md`.
- Update `.lev/pm/handoffs/20260520-formal-manifold-tooling-retool-session-1.md`.
- Do not stage or commit unless explicitly requested.

Forbidden:

- Do not route more wiki batches as a substitute for engine/manifold construction.
- Do not call schedule pseudo-basins real attractor basins.
- Do not claim PEPS/PEPS3D/full tensor-network evidence without real dynamics.
- Do not claim full E=16 from E=8 metadata or product-substrate pairing.
- Do not count decorative tool imports as full tool integration.
- Do not use NumPy in nonclassical compute paths except named classical/boundary controls.
- Do not mark the goal complete while Phi0 separation, PEPS/PEPS3D dynamics, or scale-level basin admission remains open.

Done condition:

- iter_195 spectral explanation is formally reproduced or falsified; current status: reproduced;
- spectral manifold map exists; current status: complete as bounded evidence;
- terrain/stage contribution to the slow mode is quantified; current status: complete as bounded evidence;
- bridge Phi0 is admitted by control separation or honestly killed/open; current status: open/nonrobust after coupled-E16 stress controls, not final admission;
- coupled E=16 dynamics is built or blocked with a precise receipt; current status: built as bounded dense E=16 first rung;
- full manifold trace is refreshed; current status: refreshed after Phi0 stress controls, final admission blocked;
- tensor-network dynamics advances beyond L=16 or records the exact algorithmic blocker; current status: L32 bounded low-bond first rung, L64 bounded low-bond first rung, tiny 2D PEPS first rung, and tiny 3D PEPS3D first rung complete; not full convergence or bond-scaling closure;
- PEPS/PEPS3D dynamic route is built or blocked with a precise receipt; current status: PEPS tiny 2D first rung complete and PEPS3D tiny 3D first rung complete;
- basin status is classified without overclaim;
- README and handoff are updated.

Recommended next work packet:

Build either a genuinely redesigned `Xi -> rho_AB -> Phi0` bridge mechanism or a stronger post-L64 tensor route under `system_v5/ops/formal_scouts/`.

- Preferred next packet after the L64 adaptive-bond batch, L64 cap-bias sweep, L64 two-cycle stability check, L64 fixed D6 pilot, L64 doubled-MPS deterministic pilot, PEPS/PEPS3D stage-loop depth inventory, iter_212 formalization, L4 entropy-cell witness, and causal-irreversibility `Xi` redesign: either convert the PEPS/PEPS3D depth inventory into deterministic MPDO Lindblad dynamics, invent a still-different `Xi -> rho_AB -> Phi0` mechanism that can beat time-reversed/random/terrain-erased controls, stress the doubled-MPS route with longer horizons/bond caps/trajectory-ensemble comparisons, or continue tensor progress with local Krylov batching. A larger fixed-cap surface (`D6` all families/seeds or bounded `D8`) is allowed as a diagnostic, but the D6 pilot is mixed and should not be treated as the main convergence route. Preserve that low-cap adaptive D=2/4 is bounded/biased at two cycles and non-admitting.
- If bridge work remains the priority, do not proceed to `L8_shell_weighted_phi0` as evidence on top of the failed L7 history bridge or the failed causal-irreversibility `Xi` bridge. First produce a new `Xi` family that survives the adversarial gate. Only if that passes should L8 shell-weighted be rebuilt.
- Any later L8 packet must explicitly keep `L2` chart sign, `L4` bipartite signed entropy, `L6` Hopf/Chern support, `L7` history support, and `L8` shell support separated, then test the bridge into `rho_AB` against shell/weight-shuffled, slow-mode-erased, n-hat-erased, terrain-erased, weak/strong coupling, response-gradient, random matched-norm, time-reversed, and tensor-carrier challenge controls.

Keep scale-level basin admission and final manifold admission blocked unless their own dynamic receipts exist.
