# Sim Inventory Index

Generated: `2026-06-01T18:30:06.665145+00:00`

Boundary: inventory only. This does not admit, promote, or validate a sim.

Tracked JSON keeps summary and samples by default; run with `--include-rows` for local full-row audits.

## Summary

- Sim source files indexed: `4055`
- Result JSON files seen: `2483`
- Bulk a2_state result JSON files skipped: `0`
- Linked result JSON files: `329`
- Unlinked result JSON files: `2154`
- Historical admission records: `6842`
- Admitted evidence linked rows: `89`
- Admission rows with bulk a2_state result skipped: `0`
- Repair / rerun candidate rows: `233`
- Source-only rows: `3691`

## Public Status Counts

Inventory only proves `exists`; it does not execute sims or promote results.

- `exists`: 4055

## Sim Execution Lane Counts

- `unknown`: 1782
- `mixed_or_ambiguous`: 784
- `classical`: 706
- `nonclassical`: 567
- `semiclassical_bridge`: 189
- `semiclassical_szilard`: 27

## Runner Execution Kind Counts

These use the repo runner contract vocabulary while detailed lane labels remain inventory-only signals.

- `unknown`: 2566
- `classical`: 706
- `nonclassical`: 567
- `bridge`: 216

## Engine Type Counts

- `none`: 3906
- `szilard`: 86
- `carnot`: 68
- `landauer`: 19

## Engine Role Mode Counts

- `unspecified`: 2027
- `boundary_to_nonclassical_signal`: 1128
- `negative_space_or_graveyard_control`: 1099
- `full_run_signal`: 499
- `landauer_erasure_signal`: 40

## Engine Role Counts

- `not_engine_related`: 1815
- `nonclassical_inspiration_or_boundary_signal`: 1607
- `negative_space_or_graveyard_control_signal`: 1099
- `semiclassical_szilard_engine_token_match`: 105
- `classical_carnot_engine_token_match`: 68

## Cleanup Bucket Counts

- `source_only_rerun_or_archive_decision`: 2077
- `source_only_negative_or_graveyard_manifest_before_archive_decision`: 1614
- `rerun_or_admission_candidate_review`: 126
- `keep_admitted_receipt_linked`: 89
- `late_stage_blocked_decompose_before_rerun`: 57
- `repair_admission_result_link`: 42
- `tool_depth_repair_before_admission`: 31
- `legacy_result_repair_or_quarantine`: 19

## Promotion Blocker Counts

- `wizard_admission_missing`: 3924
- `result_contract_shape_missing`: 3747
- `linked_result_missing`: 3732
- `execution_lane_metadata_missing_or_derived`: 1782
- `late_stage_signal_requires_gate_and_decomposition`: 1082
- `execution_lane_conflict_requires_manual_review`: 960
- `nonclassical_requires_local_load_bearing_pytorch`: 427
- `classical_baseline_cannot_support_bridge_or_nonclassical_promotion`: 191
- `source_tool_manifest_missing`: 172
- `source_tool_integration_depth_missing`: 152
- `load_bearing_tool_depth_missing`: 113
- `wizard_admission_admission_missing_result_link`: 42
- `numpy_load_bearing_blocked_for_bridge_or_nonclassical`: 20

## Garbage Candidate Flag Counts

- `source_only_negative_or_graveyard`: 1614
- `late_stage_unadmitted`: 1082
- `ambiguous_execution_lane`: 960
- `nonclassical_missing_load_bearing_pytorch`: 427
- `negative_probe_has_bridge_signal`: 83
- `canonical_result_not_execution_lane_evidence`: 72
- `legacy_result_or_repair_needed`: 29
- `bridge_or_nonclassical_numpy_load_bearing`: 20

## Inventory Status Counts

- `source_only`: 3691
- `rerun_or_admission_candidate`: 167
- `admitted`: 89
- `admission_missing_result_link`: 42
- `contract_shaped_but_tool_depth_thin`: 37
- `legacy_result_or_repair_needed`: 29

## Family Counts

- `graveyard_negative`: 1711
- `classical_baseline`: 1164
- `root_admission`: 862
- `weyl_spinor_clifford`: 816
- `channel_operator`: 804
- `geometry_gstack_gtower`: 743
- `axis_bridge`: 685
- `gerbe_dirac_mera_spectral`: 672
- `hopf_torus`: 656
- `entropy_information`: 602
- `density_carrier`: 519
- `thermo_engine`: 462
- `graph_topology`: 413
- `uncategorized`: 343
- `fep_holodeck_igt`: 242

## Load-Bearing Tool Counts

- `pytorch`: 966
- `z3`: 744
- `sympy`: 569
- `cvc5`: 504
- `clifford`: 279
- `rustworkx`: 273
- `numpy`: 207
- `xgi`: 202
- `gudhi`: 113
- `toponetx`: 110
- `geomstats`: 107
- `scipy`: 61
- `e3nn`: 56
- `qutip`: 43
- `qiskit`: 18
- `networkx`: 4

## Unlinked Result Samples

- `system_v4/a2_state/sim_results/deep_geometric_audit_results.json`
- `system_v4/a2_state/sim_results/holodeck_fep_results.json`
- `system_v4/a2_state/sim_results/type2_process_cycle_results.json`
- `system_v4/probes/a2_state/sim_results/L0_hopf_manifold_results.json`
- `system_v4/probes/a2_state/sim_results/boundary_flux_to_pauli_admissibility_results.json`
- `system_v4/probes/a2_state/sim_results/classical_leviathan_hobbes_stability_results.json`
- `system_v4/probes/a2_state/sim_results/prime_qit_sidecar_probe_N64_results.json`
- `system_v4/probes/a2_state/sim_results/sim_runner_taxonomy_audit_results.json`
- `system_v4/probes/a2_state/sim_results_archive/semantic_naming_20260523/axis0_kernel_phi0_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161846Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161846Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_02_gstack_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_03_axes_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_04_smt_cross_check_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_05_engine_traversal_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161904Z/phase_06_tool_integration_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_02_gstack_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_03_axes_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_04_smt_cross_check_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_05_engine_traversal_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T161925Z/phase_06_tool_integration_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T162052Z/phase_06_tool_integration_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T162256Z/phase_98_prime_resonance_via_totient_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T163716Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165402Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165402Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165402Z/phase_98_prime_resonance_via_totient_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165505Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165505Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165505Z/phase_02_gstack_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165528Z/phase_02_gstack_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165555Z/phase_17_fisher_information_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165630Z/phase_17_fisher_information_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165654Z/phase_22_probe_quotient_compression_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165657Z/phase_23_holonomic_gate_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165659Z/phase_27_prime_scaling_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165706Z/phase_28_stage_semantic_uniqueness_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165711Z/phase_29_prime_scaling_extreme_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T165839Z/phase_98_prime_resonance_via_totient_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_02_gstack_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_03_axes_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_04_smt_cross_check_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_05_engine_traversal_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171629Z/phase_06_tool_integration_results.json`

## Admitted Stems

- `classical_baseline_cholesky_spd`
- `classical_baseline_gram_schmidt`
- `classical_baseline_graph_laplacian_spectrum`
- `classical_baseline_qr_decomposition`
- `sim_assortativity_classical`
- `sim_bch_first_order_commutator_classical`
- `sim_betti_torus_classical`
- `sim_blackwell_comparison_classical`
- `sim_bottleneck_distance_classical`
- `sim_branch_weight_classical`
- `sim_cech_vs_rips_classical`
- `sim_characteristic_representation_classical`
- `sim_chebyshev_distinguishability_classical`
- `sim_choi_matrix_classical`
- `sim_clifford_capability`
- `sim_clique_complex_flagness_classical`
- `sim_contextuality_witness_classical`
- `sim_correlation_tensor_principal_directions_classical`
- `sim_cvc5_capability`
- `sim_eckart_young_truncated_svd_classical`
- `sim_empirical_bayes_james_stein_classical`
- `sim_euler_characteristic_classical`
- `sim_fiber_bundle_triviality_classical`
- `sim_fiedler_spectral_clustering_classical`
- `sim_geomstats_capability`
- `sim_graph_cheeger_inequality_classical`
- `sim_gtower_e_class_cartan_admissibility_shell_local`
- `sim_gudhi_capability`
- `sim_hodge_decomposition_classical`
- `sim_homogeneous_space_so3_mod_so2_classical`
- `sim_hypergraph_laplacian_spectrum_classical`
- `sim_integration_networkx_pyg_graph_roundtrip_micro`
- `sim_lattice_distributive_constraint_canonical`
- `sim_le_cam_deficiency_classical`
- `sim_line_graph_hitting_time_classical`
- `sim_low_rank_psd_approximation_classical`
- `sim_maurer_cartan_abelian_closure_classical`
- `sim_mayer_vietoris_classical`
- `sim_network_modularity_classical`
- `sim_numpy_capability`
- `sim_p_adic_comparison_crystalline_constraint_canonical`
- `sim_pagerank_classical`
- `sim_pca_variance_explained_classical`
- `sim_persistent_homology_circle_classical`
- `sim_principal_bundle_structure_constants_classical`
- `sim_principal_subspace_classical`
- `sim_pyg_dynamic_edge_werner`
- `sim_pyg_message_passing_autograd_micro`
- `sim_pytorch_autograd_gradient_micro`
- `sim_pytorch_density_entropy_gradient_micro`
- `sim_qiskit_capability`
- `sim_quadratic_reciprocity_constraint_canonical`
- `sim_qutip_capability`
- `sim_rank_nullity_theorem_constraint_canonical`
- `sim_rayleigh_quotient_extremum_classical`
- `sim_renyi_alpha_sweep_classical`
- `sim_rsa_correctness_constraint_canonical`
- `sim_rustworkx_capability`
- `sim_schur_triangularization_classical`
- `sim_sigma_algebra_constraint_canonical`
- `sim_signed_operator_variant_classical`
- `sim_simplicial_fvector_classical`
- `sim_simplicial_homology_rank_classical`
- `sim_stabilizer_formalism_classical`
- `sim_su2_so3_double_cover_entropy_gap`
- `sim_sympy_bch_4th_order`
- `sim_sympy_campbell_pauli`
- `sim_sympy_capability`
- `sim_sympy_charpoly_eigvals`
- `sim_sympy_clifford_cross_check`
- `sim_sympy_gaussian_integral`
- `sim_sympy_matrix_identity_micro`
- `sim_sympy_partial_fraction`
- `sim_toponetx_capability`
- `sim_toponetx_cell_incidence_micro`
- `sim_triangle_count_classical`
- `sim_tsallis_q_sweep_classical`
- `sim_witness_operator_classical`
- `sim_xgi_deep_higher_order_contagion`
- `sim_xgi_deep_hyperedge_motif_count`
- `sim_xgi_deep_hypergraph_clustering`
- `sim_xgi_deep_leviathan_hyperlap`
- `sim_z3_capability`
- `sim_zorns_lemma_constraint_canonical`
- `tool_capability_clifford`
- `tool_integration_clifford_weyl`
- `tool_integration_cvc5_sympy`
- `tool_integration_sympy_pyg`
- `tool_integration_toponetx_pyg`

## First Repair Candidates

| status | stem | families | load-bearing tools | result classes |
| --- | --- | --- | --- | --- |
| legacy_result_or_repair_needed | `sim_classical_axis0_entropy_gradient_flow` | entropy_information, thermo_engine, axis_bridge, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_axis6_action_handedness` | weyl_spinor_clifford, thermo_engine, axis_bridge, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_bell_state_partial_trace` | density_carrier, entropy_information, thermo_engine, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_fep_active_inference_step` | fep_holodeck_igt, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_holodeck_carrier_shell_spectrum` | graph_topology, gerbe_dirac_mera_spectral, thermo_engine, fep_holodeck_igt, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_hopf_u1_fiber_winding` | hopf_torus, thermo_engine, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_igt_nested_win_lose_cycle` | graph_topology, fep_holodeck_igt, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_landauer_jarzynski_coupled` | thermo_engine, axis_bridge, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_leviathan_coalition_formation` | fep_holodeck_igt, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_sci_method_popper_refutation_count` | root_admission, fep_holodeck_igt, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_szilard_maxwell_demon_coupled` | channel_operator, thermo_engine, axis_bridge, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `sim_classical_weyl_chirality_extraction` | channel_operator, weyl_spinor_clifford, thermo_engine, classical_baseline | - | classical_baseline |
| legacy_result_or_repair_needed | `e3nn_wigner_d_tensor_product_operator_family_fit_probe` | channel_operator, geometry_gstack_gtower, thermo_engine, axis_bridge, classical_baseline | e3nn | tool_lego_fit_probe |
| legacy_result_or_repair_needed | `followup_anomaly_investigation` | entropy_information, hopf_torus, graph_topology | - | - |
| legacy_result_or_repair_needed | `mass_stabilization_sim` | entropy_information, hopf_torus, weyl_spinor_clifford, graph_topology, axis_bridge | - | - |
| legacy_result_or_repair_needed | `qutip_mesolve_amplitude_damping_channel_fit_probe` | channel_operator, geometry_gstack_gtower, thermo_engine, axis_bridge, classical_baseline | qutip | tool_lego_fit_probe |
| legacy_result_or_repair_needed | `sim_axis7_deep_test` | channel_operator, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_7_12_audit` | channel_operator, weyl_spinor_clifford, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_anti_conflation` | channel_operator, entropy_information, hopf_torus, weyl_spinor_clifford, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_exploration_suite` | channel_operator, hopf_torus, weyl_spinor_clifford, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_hopf_geometry` | density_carrier, hopf_torus, weyl_spinor_clifford, geometry_gstack_gtower, thermo_engine, axis_bridge | - | - |
| contract_shaped_but_tool_depth_thin | `sim_bayesian_sufficiency_dpi_classical` | classical_baseline | - | classical_baseline |
| rerun_or_admission_candidate | `sim_bridge_carnot_admissibility_fence` | root_admission, thermo_engine, axis_bridge, classical_baseline, graveyard_negative | z3 | tool_lego_fit_probe |
| rerun_or_admission_candidate | `sim_bridge_landauer_erasure_bit_distinguishability` | root_admission, thermo_engine, axis_bridge | sympy, z3 | tool_lego_fit_probe |
| rerun_or_admission_candidate | `sim_bridge_szilard_landauer_floor` | root_admission, thermo_engine, axis_bridge, graveyard_negative | z3 | tool_lego_fit_probe |
| legacy_result_or_repair_needed | `sim_broad_axis_search` | thermo_engine, axis_bridge | - | - |
| rerun_or_admission_candidate | `sim_capability_pyg_isolated` | density_carrier, graph_topology, classical_baseline | pytorch | classical_baseline |
| rerun_or_admission_candidate | `sim_capability_scipy_isolated` | entropy_information, classical_baseline | scipy | classical_baseline |
| contract_shaped_but_tool_depth_thin | `sim_carnot_asymmetric_direction_graveyard` | thermo_engine, graveyard_negative | - | audit |
| rerun_or_admission_candidate | `sim_carnot_closure_diagnostic` | thermo_engine | z3 | tool_lego_fit_probe |
| rerun_or_admission_candidate | `sim_carnot_constraint_admissibility_fence` | root_admission, thermo_engine, axis_bridge, classical_baseline, graveyard_negative | sympy, z3 | tool_lego_fit_probe |
| contract_shaped_but_tool_depth_thin | `sim_carnot_two_bath_four_stroke_work_heat_bounds` | thermo_engine, classical_baseline, graveyard_negative | - | classical_baseline |
| contract_shaped_but_tool_depth_thin | `sim_classical_carnot_efficiency_vs_reservoir` | root_admission, thermo_engine, classical_baseline | - | classical_baseline |
| contract_shaped_but_tool_depth_thin | `sim_classical_landauer_erasure_cost_curve` | root_admission, thermo_engine, classical_baseline | - | classical_baseline |
| contract_shaped_but_tool_depth_thin | `sim_classical_szilard_one_bit_measurement_work` | root_admission, thermo_engine, classical_baseline | - | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_global_relative_phase_vector_rotation_nonpole_sweep` | weyl_spinor_clifford | clifford | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_bridge_claims_canonical` | channel_operator, weyl_spinor_clifford, geometry_gstack_gtower, gerbe_dirac_mera_spectral, axis_bridge, classical_baseline, graveyard_negative | cvc5, gudhi, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_emergence_quantities` | weyl_spinor_clifford, graph_topology, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_pairwise_coupling` | channel_operator, hopf_torus, weyl_spinor_clifford, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_topology_variants` | weyl_spinor_clifford, graph_topology, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_triple_coexistence` | weyl_spinor_clifford, graph_topology, gerbe_dirac_mera_spectral, graveyard_negative | gudhi, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_hopf_outer_rotation_readout` | hopf_torus, weyl_spinor_clifford | clifford | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_hopf_weyl_fiber_horizontal_base_tangent_inner_product` | hopf_torus, weyl_spinor_clifford | clifford | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_hopf_weyl_vertical_horizontal_tangent_projection_sweep` | hopf_torus, weyl_spinor_clifford | clifford | classical_baseline |
| rerun_or_admission_candidate | `sim_conditional_entropy_torch_separation_microfit` | root_admission, entropy_information, geometry_gstack_gtower, thermo_engine, axis_bridge, classical_baseline | pytorch | tool_lego_fit_probe |
| legacy_result_or_repair_needed | `sim_constrain_legos_L0` | root_admission, channel_operator, entropy_information, thermo_engine | - | - |
| rerun_or_admission_candidate | `sim_constraint_admissibility_fence_cvc5_microfit` | root_admission, density_carrier, channel_operator, geometry_gstack_gtower, thermo_engine, axis_bridge, classical_baseline | cvc5 | tool_lego_fit_probe |
| rerun_or_admission_candidate | `sim_constraint_manifold_L0_L1` | root_admission, channel_operator, geometry_gstack_gtower, axis_bridge | sympy, z3 | supporting |
| legacy_result_or_repair_needed | `sim_constraint_manifold_L4_L5_L6` | channel_operator, weyl_spinor_clifford, geometry_gstack_gtower | numpy, sympy | - |
| legacy_result_or_repair_needed | `sim_constraint_manifold_L7_L8_L9` | geometry_gstack_gtower, axis_bridge | - | - |

## First Garbage Candidate Flags

| flags | stem | lane | cleanup bucket | blockers |
| --- | --- | --- | --- | --- |
| nonclassical_missing_load_bearing_pytorch | `abiogenesis_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| nonclassical_missing_load_bearing_pytorch | `abiogenesis_v2_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, negative_probe_has_bridge_signal, source_only_negative_or_graveyard | `axis0_bridge_owner_alignment_contract` | `semiclassical_bridge` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, negative_probe_has_bridge_signal, source_only_negative_or_graveyard | `axis0_bridge_owner_packet_surface` | `semiclassical_bridge` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis0_composition_scaffold` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis0_constraint_types` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch, source_only_negative_or_graveyard | `axis0_correlation_sim` | `nonclassical` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_full_constraint_manifold_audit` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_full_constraint_manifold_guardrail_sim` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_full_spectrum_sim` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, negative_probe_has_bridge_signal, source_only_negative_or_graveyard | `axis0_gradient_sim` | `semiclassical_bridge` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted | `axis0_lambda_crosslane_semantic_core` | `semiclassical_bridge` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted | `axis0_option_spectrum_sim` | `semiclassical_bridge` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis0_path_integral_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis0_result_loader` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted, source_only_negative_or_graveyard | `axis0_xi_bakeoff_sim` | `mixed_or_ambiguous` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted | `axis0_xi_law_fingerprint` | `semiclassical_bridge` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_xi_strict_bakeoff_sim` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis3_4_nondegen_diagnostic_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis3_orthogonality_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis5_discrete_calculus_rosetta_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis_6_precedence_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted | `axis_7_12_commutator_construction_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_7_12_mirror_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_7_12_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_compositional_structure_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_interaction_matrix` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis_lie_closure_expansion_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis_relations_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted | `axis_residual_subspace_discovery_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_triplet_orthogonality_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_triplet_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing |
| nonclassical_missing_load_bearing_pytorch | `big_bang_fuzz_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| nonclassical_missing_load_bearing_pytorch | `chemistry_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_local_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| ambiguous_execution_lane | `classical_baseline_cholesky_spd` | `classical` | `keep_admitted_receipt_linked` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing |
| ambiguous_execution_lane | `classical_baseline_gram_schmidt` | `classical` | `keep_admitted_receipt_linked` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing |
| ambiguous_execution_lane | `classical_baseline_graph_laplacian_spectrum` | `classical` | `keep_admitted_receipt_linked` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing |
| ambiguous_execution_lane | `classical_baseline_hopf_fibration` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, linked_result_missing, result_contract_shape_missing, wizard_admission_missing |
| ambiguous_execution_lane | `classical_baseline_qr_decomposition` | `classical` | `keep_admitted_receipt_linked` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing |
| ambiguous_execution_lane | `classical_baseline_simpson_integration` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, linked_result_missing, result_contract_shape_missing, wizard_admission_missing |
| ambiguous_execution_lane | `classical_baseline_szilard_onebit` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, linked_result_missing, result_contract_shape_missing, wizard_admission_missing |
| ambiguous_execution_lane, late_stage_unadmitted, legacy_result_or_repair_needed | `sim_classical_axis0_entropy_gradient_flow` | `classical` | `late_stage_blocked_decompose_before_rerun` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, load_bearing_tool_depth_missing |
| ambiguous_execution_lane, late_stage_unadmitted, legacy_result_or_repair_needed | `sim_classical_axis6_action_handedness` | `classical` | `late_stage_blocked_decompose_before_rerun` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, load_bearing_tool_depth_missing |
| ambiguous_execution_lane, legacy_result_or_repair_needed | `sim_classical_bell_state_partial_trace` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing, source_tool_integration_depth_missing |
| legacy_result_or_repair_needed | `sim_classical_fep_active_inference_step` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, load_bearing_tool_depth_missing, source_tool_integration_depth_missing, source_tool_manifest_missing |
| legacy_result_or_repair_needed | `sim_classical_holodeck_carrier_shell_spectrum` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, load_bearing_tool_depth_missing, source_tool_integration_depth_missing, source_tool_manifest_missing |
| ambiguous_execution_lane, legacy_result_or_repair_needed | `sim_classical_hopf_u1_fiber_winding` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing, source_tool_integration_depth_missing |
| legacy_result_or_repair_needed | `sim_classical_igt_nested_win_lose_cycle` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, load_bearing_tool_depth_missing, source_tool_integration_depth_missing, source_tool_manifest_missing |
| ambiguous_execution_lane, legacy_result_or_repair_needed | `sim_classical_landauer_jarzynski_coupled` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing, source_tool_integration_depth_missing |

## First Cleanup Buckets

| bucket | stem | lane | engine types | role modes | public status |
| --- | --- | --- | --- | --- | --- |
| keep_admitted_receipt_linked | `classical_baseline_cholesky_spd` | `classical` | none | boundary_to_nonclassical_signal | `exists` |
| keep_admitted_receipt_linked | `classical_baseline_gram_schmidt` | `classical` | none | boundary_to_nonclassical_signal | `exists` |
| keep_admitted_receipt_linked | `classical_baseline_graph_laplacian_spectrum` | `classical` | none | boundary_to_nonclassical_signal | `exists` |
| late_stage_blocked_decompose_before_rerun | `sim_classical_axis0_entropy_gradient_flow` | `classical` | none | unspecified | `exists` |
| late_stage_blocked_decompose_before_rerun | `sim_classical_axis6_action_handedness` | `classical` | none | unspecified | `exists` |
| late_stage_blocked_decompose_before_rerun | `sim_axis7_deep_test` | `unknown` | none | full_run_signal | `exists` |
| legacy_result_repair_or_quarantine | `sim_classical_bell_state_partial_trace` | `classical` | none | unspecified | `exists` |
| legacy_result_repair_or_quarantine | `sim_classical_fep_active_inference_step` | `classical` | none | unspecified | `exists` |
| legacy_result_repair_or_quarantine | `sim_classical_holodeck_carrier_shell_spectrum` | `classical` | none | unspecified | `exists` |
| repair_admission_result_link | `sim_axiom_n01_composition_order_distinguishes` | `unknown` | none | unspecified | `exists` |
| repair_admission_result_link | `sim_blackwell_sufficiency_order_classical` | `classical` | none | unspecified | `exists` |
| repair_admission_result_link | `sim_clifford_deep_cl3_rotor_double_cover` | `nonclassical` | none | negative_space_or_graveyard_control | `exists` |
| rerun_or_admission_candidate_review | `sim_capability_pyg_isolated` | `classical` | none | unspecified | `exists` |
| rerun_or_admission_candidate_review | `sim_capability_scipy_isolated` | `classical` | none | boundary_to_nonclassical_signal, negative_space_or_graveyard_control | `exists` |
| rerun_or_admission_candidate_review | `sim_carnot_closure_diagnostic` | `mixed_or_ambiguous` | carnot | full_run_signal, boundary_to_nonclassical_signal, negative_space_or_graveyard_control | `exists` |
| source_only_negative_or_graveyard_manifest_before_archive_decision | `axis0_bridge_owner_alignment_contract` | `semiclassical_bridge` | none | boundary_to_nonclassical_signal | `exists` |
| source_only_negative_or_graveyard_manifest_before_archive_decision | `axis0_bridge_owner_packet_surface` | `semiclassical_bridge` | none | boundary_to_nonclassical_signal | `exists` |
| source_only_negative_or_graveyard_manifest_before_archive_decision | `axis0_correlation_sim` | `nonclassical` | none | negative_space_or_graveyard_control | `exists` |
| source_only_rerun_or_archive_decision | `abiogenesis_sim` | `nonclassical` | none | unspecified | `exists` |
| source_only_rerun_or_archive_decision | `abiogenesis_v2_sim` | `nonclassical` | none | unspecified | `exists` |
| source_only_rerun_or_archive_decision | `alignment_sim` | `unknown` | none | full_run_signal | `exists` |
| tool_depth_repair_before_admission | `sim_bayesian_sufficiency_dpi_classical` | `classical` | none | boundary_to_nonclassical_signal | `exists` |
| tool_depth_repair_before_admission | `sim_carnot_asymmetric_direction_graveyard` | `classical` | carnot | negative_space_or_graveyard_control | `exists` |
| tool_depth_repair_before_admission | `sim_carnot_two_bath_four_stroke_work_heat_bounds` | `classical` | carnot | full_run_signal, boundary_to_nonclassical_signal, negative_space_or_graveyard_control | `exists` |
