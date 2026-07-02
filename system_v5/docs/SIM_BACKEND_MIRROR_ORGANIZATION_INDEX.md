# Sim Backend Mirror Organization Index

Generated: `2026-06-01T18:37:04.724175+00:00`

Boundary: organization only. This does not rerun, admit, promote, or complete any sim.

This index organizes by target object family plus backend mirror state. Folder/estate is secondary.

## Summary

- Source files indexed: `5327`
- Active source files indexed: `966`
- Backend states: `{'no_numeric_backend_detected': 999, 'pytorch_only': 2628, 'dual_pytorch_jax': 114, 'jax_only': 46, 'numpy_or_classical_only': 1540}`
- Mirror statuses over active source clusters: `{'missing_jax_mirror': 611, 'has_pytorch_and_jax_surface': 116, 'missing_pytorch_mirror': 44, 'missing_both_primary_backends': 180}`
- Estate counts: `{'active_formal_scout': 926, 'lego': 40, 'legacy_v4_probe': 4270, 'retired_exploration': 91}`

## How To Use This Index

1. Pick the mathematical object family, not the folder.
2. Pick one source row or cluster.
3. Check whether PyTorch, JAX, or both are present.
4. If only one backend exists, write or repair the mirror before treating the row as a dual-engine result.
5. Check the result receipt and formal readiness status before citing the sim.
6. For retired exploration rows, port the idea into active v5 scout/lego form before using it as evidence.

## Family Counts

| family | count | pytorch | jax | dual | numpy/control | no numeric | active | legacy | retired |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `uncategorized` | 2342 | 937 | 3 | 3 | 808 | 591 | 34 | 2243 | 65 |
| `classical_baseline` | 534 | 225 | 0 | 0 | 269 | 40 | 2 | 531 | 1 |
| `finite_probe_response` | 515 | 295 | 19 | 60 | 28 | 113 | 449 | 65 | 1 |
| `axis0_xi_phi_bridge` | 485 | 284 | 0 | 0 | 156 | 45 | 72 | 407 | 6 |
| `shell_possibility_field` | 289 | 241 | 0 | 2 | 14 | 32 | 14 | 275 | 0 |
| `entropy_qit_readout` | 145 | 77 | 1 | 10 | 48 | 9 | 49 | 94 | 2 |
| `clifford_quaternion_rotor` | 143 | 82 | 4 | 9 | 35 | 13 | 46 | 97 | 0 |
| `mps_peps_peps3d_carrier` | 116 | 93 | 0 | 5 | 1 | 17 | 113 | 3 | 0 |
| `g_structure_candidate` | 110 | 83 | 1 | 6 | 18 | 2 | 17 | 93 | 0 |
| `alt_geometry_candidate` | 103 | 77 | 4 | 3 | 13 | 6 | 24 | 79 | 0 |
| `tool_microprobe` | 99 | 24 | 9 | 0 | 39 | 27 | 9 | 88 | 2 |
| `formal_validator_meta` | 92 | 18 | 0 | 0 | 21 | 53 | 15 | 67 | 10 |
| `operator_channel_action` | 86 | 29 | 1 | 4 | 43 | 9 | 14 | 69 | 3 |
| `hopf_connection_holonomy` | 81 | 71 | 0 | 3 | 3 | 4 | 10 | 71 | 0 |
| `left_right_weyl_chirality` | 71 | 29 | 2 | 3 | 22 | 15 | 26 | 45 | 0 |
| `attractor_basin_world_model` | 61 | 37 | 0 | 0 | 6 | 18 | 51 | 10 | 0 |
| `nested_hopf_tori` | 27 | 8 | 1 | 3 | 11 | 4 | 10 | 17 | 0 |
| `terrain_weyl_law` | 14 | 9 | 0 | 2 | 3 | 0 | 4 | 9 | 1 |
| `spinor_density_carrier` | 8 | 6 | 0 | 1 | 1 | 0 | 5 | 3 | 0 |
| `hopf_fibration` | 6 | 3 | 1 | 0 | 1 | 1 | 2 | 4 | 0 |

## Mirror Gap Samples

These are not all gaps. They are the first high-value active clusters where one primary backend is missing.

| family | object key | status | sources |
| --- | --- | --- | --- |
| `alt_geometry_candidate` | `finite_projective_design_spectral_triple_gate` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_finite_projective_design_spectral_triple_gate_probe.py` |
| `alt_geometry_candidate` | `geom_dirac_monopole_u1` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_dirac_monopole_u1_deep_probe.py` |
| `alt_geometry_candidate` | `geom_dirac_monopole_u1_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_dirac_monopole_u1_codex_probe.py` |
| `alt_geometry_candidate` | `geom_spectral_triple` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_spectral_triple_deep_probe.py` |
| `alt_geometry_candidate` | `geom_spectral_triple_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_spectral_triple_codex_probe.py` |
| `alt_geometry_candidate` | `geom_twistor_incidence_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_twistor_incidence_codex_probe.py` |
| `alt_geometry_candidate` | `geometry_dirac_monopole_u1` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_dirac_monopole_u1_probe.py` |
| `alt_geometry_candidate` | `geometry_seiberg_witten_8d` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_seiberg_witten_8d_probe.py` |
| `alt_geometry_candidate` | `geometry_spectral_triple` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_spectral_triple_probe.py` |
| `alt_geometry_candidate` | `geometry_twistor_incidence_spinor_geometry` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_twistor_incidence_spinor_geometry_probe.py` |
| `alt_geometry_candidate` | `gstruct_seiberg_witten_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_gstruct_seiberg_witten_codex_probe.py` |
| `alt_geometry_candidate` | `hitchin_higgs_spectral_triples_module` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/claude_integrated_manifold_modules/hitchin_higgs_spectral_triples_module.py` |
| `alt_geometry_candidate` | `spinor_twistor_entanglement_information_network_root_gate` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_spinor_twistor_entanglement_information_network_root_gate_probe.py` |
| `alt_geometry_candidate` | `spinor_twistor_flux_basin_binding` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_spinor_twistor_flux_basin_binding_probe.py` |
| `alt_geometry_candidate` | `spinor_twistor_network_clifford_tensor_boundary_next_wave` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py` |
| `alt_geometry_candidate` | `twistor_hopf_spinor_adapter` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_twistor_hopf_spinor_adapter_probe.py` |
| `alt_geometry_candidate` | `two_point_spectral_triple_dirac_commutator_distance_sympy_z3` | `missing_jax_mirror` | `system_v5/legos/two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3.py` |
| `clifford_quaternion_rotor` | `clifford_full_cl_1_3_gamma5_chirality_replacement` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_clifford_full_cl_1_3_gamma5_chirality_replacement_probe.py` |
| `clifford_quaternion_rotor` | `clifford_quaternion_rotor_spinor_network_peps3d_quimb_sympy_z3` | `missing_jax_mirror` | `system_v5/legos/clifford_quaternion_rotor_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3.py` |
| `clifford_quaternion_rotor` | `clifford_quaternion_twistor_isolated` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_clifford_quaternion_twistor_isolated_probe.py` |
| `clifford_quaternion_rotor` | `clifford_sympy_geomstats_nested_g_structure_live_state` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_clifford_sympy_geomstats_nested_g_structure_live_state_probe.py` |
| `clifford_quaternion_rotor` | `eight_qubit_boundary_projected_gamma5_channel_coherent_information` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe.py` |
| `clifford_quaternion_rotor` | `eight_qubit_boundary_projected_gamma5_mutual_information_persistence` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe.py` |
| `clifford_quaternion_rotor` | `finite_density_hopf_spinor_clifford_channel_structure_reduction_order` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe.py` |
| `clifford_quaternion_rotor` | `gamma5_offdiagonal_coherence_persistence_rate_compression` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_gamma5_offdiagonal_coherence_persistence_rate_compression_probe.py` |
| `clifford_quaternion_rotor` | `gamma5_offdiagonal_coherence_trace_orbit_effective_channel` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_gamma5_offdiagonal_coherence_trace_orbit_effective_channel_probe.py` |
| `clifford_quaternion_rotor` | `gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel_probe.py` |
| `clifford_quaternion_rotor` | `gamma5_offdiagonal_coherence_trace_orbit_threshold_sweep` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_gamma5_offdiagonal_coherence_trace_orbit_threshold_sweep_probe.py` |
| `clifford_quaternion_rotor` | `geom_clifford_algebra` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_clifford_algebra_deep_probe.py` |
| `clifford_quaternion_rotor` | `geom_clifford_algebra_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_clifford_algebra_codex_probe.py` |
| `clifford_quaternion_rotor` | `geom_clifford_torus_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_clifford_torus_codex_probe.py` |
| `clifford_quaternion_rotor` | `geom_quaternion_sphere` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_quaternion_sphere_deep_probe.py` |
| `clifford_quaternion_rotor` | `geom_quaternion_sphere_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_geom_quaternion_sphere_codex_probe.py` |
| `clifford_quaternion_rotor` | `geometry_clifford_geometries_cl3_cl6` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_clifford_geometries_cl3_cl6_probe.py` |
| `clifford_quaternion_rotor` | `geometry_clifford_torus_t2_in_s3` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_clifford_torus_t2_in_s3_probe.py` |
| `clifford_quaternion_rotor` | `geometry_su2_spin3_unit_quaternion_double_cover` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_geometry_su2_spin3_unit_quaternion_double_cover_probe.py` |
| `clifford_quaternion_rotor` | `gstruct_clifford_module_codex` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_gstruct_clifford_module_codex_probe.py` |
| `clifford_quaternion_rotor` | `l3_clifford_quaternion_invariant_layer` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/sim_l3_clifford_quaternion_invariant_layer_probe.py` |
| `clifford_quaternion_rotor` | `l3_quaternion_clifford_orientation_layer` | `missing_pytorch_mirror` | `system_v5/ops/formal_scouts/sim_jax_native_l3_quaternion_clifford_orientation_layer_probe.py` |
| `clifford_quaternion_rotor` | `persistence_and_clifford_projection_feedback` | `missing_jax_mirror` | `system_v5/ops/formal_scouts/claude_integrated_manifold_modules/persistence_and_clifford_projection_feedback.py` |

## Next Action Queue

These are routing queues, not execution claims.

| queue | count | first examples |
| --- | --- | --- |
| `repair_jax_mirrors_for_pytorch_active_high_value` | 487 | `alt_geometry_candidate::finite_projective_design_spectral_triple_gate`<br>`alt_geometry_candidate::geom_dirac_monopole_u1`<br>`alt_geometry_candidate::geom_dirac_monopole_u1_codex` |
| `repair_pytorch_mirrors_for_jax_active_high_value` | 32 | `alt_geometry_candidate::geometry_dirac_monopole_u1`<br>`alt_geometry_candidate::geometry_seiberg_witten_8d`<br>`alt_geometry_candidate::geometry_spectral_triple` |
| `write_explicit_dual_backend_comparison_receipts` | 2 | `entropy_qit_readout::l6_entropy_cut_communication_layer`<br>`finite_probe_response::l4_terrain_channel_generator_layer` |
| `add_or_repair_result_receipts` | 80 | `system_v5/ops/formal_scouts/claude_integrated_manifold_modules/chirality_projected_cuts_and_persistence_weighted_feedback.py`<br>`system_v5/ops/formal_scouts/claude_integrated_manifold_modules/feedback_graveyards_and_connection_holonomy.py`<br>`system_v5/ops/formal_scouts/claude_integrated_manifold_modules/hitchin_higgs_spectral_triples_module.py` |
| `fix_or_preserve_formal_validator_red` | 295 | `system_v5/ops/formal_scouts/sim_active_policy_online_vmp_margin_closure_probe.py`<br>`system_v5/ops/formal_scouts/sim_aligned_model_adapter_matrix_shell_probe.py`<br>`system_v5/ops/formal_scouts/sim_antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe.py` |
| `port_retired_exploration_only_if_still_wanted` | 7 | `system_v5/grok_sim/loop_runner/contracts/phase_10_entropy_monotonicity.py`<br>`system_v5/grok_sim/loop_runner/contracts/phase_19_terrain_operations.py`<br>`system_v5/grok_sim/loop_runner/contracts/phase_20_16stages_4substages.py` |

## Active Rule

A PyTorch/JAX pair is useful only when both sides compute the same named finite map or readout and a receipt compares them. A JAX-only or PyTorch-only row is still usable, but its next action is mirror repair, not composition or layer completion.

Machine index: `system_v5/evidence/sim_backend_mirror_organization_index.json`
