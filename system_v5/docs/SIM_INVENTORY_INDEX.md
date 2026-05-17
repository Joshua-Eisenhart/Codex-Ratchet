# Sim Inventory Index

Generated: `2026-05-17T04:51:39.664346+00:00`

Boundary: inventory only. This does not admit, promote, or validate a sim.

Tracked JSON keeps summary and samples by default; run with `--include-rows` for local full-row audits.

## Summary

- Sim source files indexed: `10855`
- Result JSON files seen: `1442`
- Bulk a2_state result JSON files skipped: `7052`
- Linked result JSON files: `73`
- Unlinked result JSON files: `1369`
- Wizard-admitted stems: `0`
- Repair / rerun candidate rows: `72`
- Source-only rows: `3959`

## Public Status Counts

Inventory only proves `exists`; it does not execute sims or promote results.

- `exists`: 10855

## Sim Execution Lane Counts

- `unknown`: 5687
- `nonclassical`: 3381
- `mixed_or_ambiguous`: 813
- `classical`: 732
- `semiclassical_bridge`: 205
- `semiclassical_szilard`: 37

## Runner Execution Kind Counts

These use the repo runner contract vocabulary while detailed lane labels remain inventory-only signals.

- `unknown`: 6500
- `nonclassical`: 3381
- `classical`: 732
- `bridge`: 242

## Engine Type Counts

- `none`: 10694
- `szilard`: 88
- `carnot`: 70
- `landauer`: 21

## Engine Role Mode Counts

- `unspecified`: 7605
- `negative_space_or_graveyard_control`: 1525
- `full_run_signal`: 1264
- `boundary_to_nonclassical_signal`: 982
- `landauer_erasure_signal`: 41

## Engine Role Counts

- `not_engine_related`: 5498
- `nonclassical_inspiration_or_boundary_signal`: 4270
- `negative_space_or_graveyard_control_signal`: 1525
- `semiclassical_szilard_engine_token_match`: 109
- `classical_carnot_engine_token_match`: 70

## Cleanup Bucket Counts

- `repair_admission_result_link`: 6824
- `source_only_rerun_or_archive_decision`: 2279
- `source_only_negative_or_graveyard_manifest_before_archive_decision`: 1680
- `late_stage_blocked_decompose_before_rerun`: 50
- `legacy_result_repair_or_quarantine`: 13
- `rerun_or_admission_candidate_review`: 9

## Promotion Blocker Counts

- `result_contract_shape_missing`: 10793
- `linked_result_missing`: 10782
- `wizard_admission_admission_missing_result_link`: 6824
- `execution_lane_metadata_missing_or_derived`: 5687
- `wizard_admission_missing`: 4031
- `nonclassical_requires_load_bearing_pytorch`: 3173
- `late_stage_signal_requires_gate_and_decomposition`: 1126
- `execution_lane_conflict_requires_manual_review`: 856
- `source_tool_manifest_missing`: 243
- `numpy_load_bearing_blocked_for_bridge_or_nonclassical`: 227
- `source_tool_integration_depth_missing`: 207
- `classical_baseline_cannot_support_bridge_or_nonclassical_promotion`: 56
- `load_bearing_tool_depth_missing`: 27

## Garbage Candidate Flag Counts

- `nonclassical_missing_load_bearing_pytorch`: 3173
- `source_only_negative_or_graveyard`: 1680
- `late_stage_unadmitted`: 1126
- `ambiguous_execution_lane`: 856
- `bridge_or_nonclassical_numpy_load_bearing`: 227
- `negative_probe_has_bridge_signal`: 81
- `legacy_result_or_repair_needed`: 23
- `canonical_result_not_execution_lane_evidence`: 6

## Inventory Status Counts

- `admission_missing_result_link`: 6824
- `source_only`: 3959
- `rerun_or_admission_candidate`: 46
- `legacy_result_or_repair_needed`: 23
- `contract_shaped_but_tool_depth_thin`: 3

## Family Counts

- `hopf_torus`: 2902
- `weyl_spinor_clifford`: 2802
- `channel_operator`: 2169
- `uncategorized`: 1937
- `graph_topology`: 1847
- `graveyard_negative`: 1750
- `density_carrier`: 1269
- `classical_baseline`: 1188
- `root_admission`: 895
- `geometry_gstack_gtower`: 791
- `axis_bridge`: 733
- `gerbe_dirac_mera_spectral`: 699
- `entropy_information`: 615
- `thermo_engine`: 488
- `fep_holodeck_igt`: 242

## Load-Bearing Tool Counts

- `z3`: 7388
- `pytorch`: 1587
- `sympy`: 1012
- `cvc5`: 972
- `rustworkx`: 765
- `clifford`: 763
- `numpy`: 693
- `xgi`: 677
- `geomstats`: 597
- `toponetx`: 577
- `gudhi`: 563
- `pyg`: 550
- `scipy`: 548
- `qutip`: 544
- `qiskit`: 506
- `e3nn`: 54
- `networkx`: 3

## Unlinked Result Samples

- `system_v4/a2_state/sim_results/deep_geometric_audit_results.json`
- `system_v4/a2_state/sim_results/holodeck_fep_results.json`
- `system_v4/a2_state/sim_results/type2_process_cycle_results.json`
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
- `system_v5/grok_sim/loop_runner/receipts/20260513T171852Z/phase_00_smoke_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171852Z/phase_01_axioms_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171852Z/phase_02_gstack_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171852Z/phase_03_axes_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171852Z/phase_04_smt_cross_check_results.json`
- `system_v5/grok_sim/loop_runner/receipts/20260513T171852Z/phase_05_engine_traversal_results.json`

## Admitted Stems

- none

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
| legacy_result_or_repair_needed | `followup_anomaly_investigation` | entropy_information, hopf_torus, graph_topology | - | - |
| legacy_result_or_repair_needed | `mass_stabilization_sim` | entropy_information, hopf_torus, weyl_spinor_clifford, graph_topology, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis7_deep_test` | channel_operator, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_7_12_audit` | channel_operator, weyl_spinor_clifford, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_anti_conflation` | channel_operator, entropy_information, hopf_torus, weyl_spinor_clifford, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_exploration_suite` | channel_operator, hopf_torus, weyl_spinor_clifford, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_axis_hopf_geometry` | density_carrier, hopf_torus, weyl_spinor_clifford, geometry_gstack_gtower, thermo_engine, axis_bridge | - | - |
| legacy_result_or_repair_needed | `sim_broad_axis_search` | thermo_engine, axis_bridge | - | - |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_bridge_claims_canonical` | channel_operator, weyl_spinor_clifford, geometry_gstack_gtower, gerbe_dirac_mera_spectral, axis_bridge, classical_baseline, graveyard_negative | cvc5, gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_emergence_quantities` | weyl_spinor_clifford, graph_topology, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_pairwise_coupling` | channel_operator, hopf_torus, weyl_spinor_clifford, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_topology_variants` | weyl_spinor_clifford, graph_topology, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_clifford_holo_dirac_triple_coexistence` | weyl_spinor_clifford, graph_topology, gerbe_dirac_mera_spectral, graveyard_negative | gudhi, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_contact_holo_weyl_bridge_claims_canonical` | density_carrier, weyl_spinor_clifford, geometry_gstack_gtower, graph_topology, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_contact_holo_weyl_emergence_quantities` | weyl_spinor_clifford, geometry_gstack_gtower, graph_topology, gerbe_dirac_mera_spectral | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_contact_holo_weyl_pairwise_coupling` | hopf_torus, weyl_spinor_clifford, geometry_gstack_gtower, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_contact_holo_weyl_topology_variants` | weyl_spinor_clifford, geometry_gstack_gtower, graph_topology, gerbe_dirac_mera_spectral, classical_baseline, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_contact_holo_weyl_triple_coexistence` | entropy_information, weyl_spinor_clifford, geometry_gstack_gtower, graph_topology, gerbe_dirac_mera_spectral | rustworkx, toponetx, xgi | classical_baseline |
| legacy_result_or_repair_needed | `sim_corrected_axes` | hopf_torus, geometry_gstack_gtower, axis_bridge, graveyard_negative | - | - |
| rerun_or_admission_candidate | `sim_decuple_coupling_program` | hopf_torus, weyl_spinor_clifford, geometry_gstack_gtower, gerbe_dirac_mera_spectral | pytorch, sympy, z3 | canonical |
| rerun_or_admission_candidate | `sim_general_n_product_zero_theorem` | graveyard_negative | pytorch, sympy, z3 | canonical |
| rerun_or_admission_candidate | `sim_hopf_contact_gerbe_bridge_claims_canonical` | density_carrier, hopf_torus, geometry_gstack_gtower, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | cvc5, gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_contact_gerbe_emergence_quantities` | hopf_torus, geometry_gstack_gtower, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_contact_gerbe_pairwise_coupling` | hopf_torus, geometry_gstack_gtower, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_contact_gerbe_topology_variants` | hopf_torus, geometry_gstack_gtower, gerbe_dirac_mera_spectral | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_contact_gerbe_triple_coexistence` | hopf_torus, geometry_gstack_gtower, gerbe_dirac_mera_spectral, graveyard_negative | rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_mera_gerbe_bridge_claims_canonical` | density_carrier, hopf_torus, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | cvc5, gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_mera_gerbe_emergence_quantities` | hopf_torus, gerbe_dirac_mera_spectral, axis_bridge | gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_mera_gerbe_pairwise_coupling` | hopf_torus, gerbe_dirac_mera_spectral, graveyard_negative | gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_mera_gerbe_topology_variants` | hopf_torus, gerbe_dirac_mera_spectral | gudhi, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_hopf_mera_gerbe_triple_coexistence` | hopf_torus, gerbe_dirac_mera_spectral, graveyard_negative | gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| legacy_result_or_repair_needed | `sim_missing_axis_search` | channel_operator, hopf_torus, weyl_spinor_clifford, axis_bridge | - | - |
| rerun_or_admission_candidate | `sim_nonuple_coupling_program` | hopf_torus, weyl_spinor_clifford, geometry_gstack_gtower, gerbe_dirac_mera_spectral | clifford, pytorch, sympy, z3 | canonical |
| rerun_or_admission_candidate | `sim_octuple_coupling_program` | hopf_torus, weyl_spinor_clifford, geometry_gstack_gtower, gerbe_dirac_mera_spectral | clifford, pytorch, sympy, z3 | canonical |
| rerun_or_admission_candidate | `sim_septuple_coupling_program` | hopf_torus, weyl_spinor_clifford, gerbe_dirac_mera_spectral | clifford, pytorch, sympy, z3 | canonical |
| rerun_or_admission_candidate | `sim_st_dirac_symplectic_bridge_claims_canonical` | density_carrier, geometry_gstack_gtower, gerbe_dirac_mera_spectral, axis_bridge, graveyard_negative | cvc5, gudhi, pyg, rustworkx, toponetx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_st_dirac_symplectic_emergence_quantities` | geometry_gstack_gtower, gerbe_dirac_mera_spectral, axis_bridge, classical_baseline, graveyard_negative | rustworkx, xgi | classical_baseline |
| rerun_or_admission_candidate | `sim_st_dirac_symplectic_pairwise_coupling` | geometry_gstack_gtower, gerbe_dirac_mera_spectral, classical_baseline, graveyard_negative | pyg, rustworkx, xgi | classical_baseline |

## First Garbage Candidate Flags

| flags | stem | lane | cleanup bucket | blockers |
| --- | --- | --- | --- | --- |
| nonclassical_missing_load_bearing_pytorch | `abiogenesis_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| nonclassical_missing_load_bearing_pytorch | `abiogenesis_v2_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, negative_probe_has_bridge_signal, source_only_negative_or_graveyard | `axis0_bridge_owner_alignment_contract` | `semiclassical_bridge` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, negative_probe_has_bridge_signal, source_only_negative_or_graveyard | `axis0_bridge_owner_packet_surface` | `semiclassical_bridge` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis0_composition_scaffold` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis0_constraint_types` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch, source_only_negative_or_graveyard | `axis0_correlation_sim` | `nonclassical` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_full_constraint_manifold_audit` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_full_constraint_manifold_guardrail_sim` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_full_spectrum_sim` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, negative_probe_has_bridge_signal, source_only_negative_or_graveyard | `axis0_gradient_sim` | `semiclassical_bridge` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted | `axis0_lambda_crosslane_semantic_core` | `semiclassical_bridge` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted | `axis0_option_spectrum_sim` | `semiclassical_bridge` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis0_path_integral_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis0_result_loader` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| ambiguous_execution_lane, late_stage_unadmitted, source_only_negative_or_graveyard | `axis0_xi_bakeoff_sim` | `mixed_or_ambiguous` | `source_only_negative_or_graveyard_manifest_before_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted | `axis0_xi_law_fingerprint` | `semiclassical_bridge` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing, source_tool_integration_depth_missing |
| ambiguous_execution_lane, late_stage_unadmitted | `axis0_xi_strict_bakeoff_sim` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis3_4_nondegen_diagnostic_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis3_orthogonality_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis5_discrete_calculus_rosetta_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis_6_precedence_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted | `axis_7_12_commutator_construction_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_7_12_mirror_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_7_12_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_compositional_structure_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_interaction_matrix` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis_lie_closure_expansion_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted | `axis_relations_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted | `axis_residual_subspace_discovery_sim` | `unknown` | `source_only_rerun_or_archive_decision` | execution_lane_metadata_missing_or_derived, late_stage_signal_requires_gate_and_decomposition, linked_result_missing, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_triplet_orthogonality_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| late_stage_unadmitted, nonclassical_missing_load_bearing_pytorch | `axis_triplet_orthogonality_suite` | `nonclassical` | `source_only_rerun_or_archive_decision` | late_stage_signal_requires_gate_and_decomposition, linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing |
| nonclassical_missing_load_bearing_pytorch | `big_bang_fuzz_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| nonclassical_missing_load_bearing_pytorch | `chemistry_sim` | `nonclassical` | `source_only_rerun_or_archive_decision` | linked_result_missing, nonclassical_requires_load_bearing_pytorch, result_contract_shape_missing, source_tool_integration_depth_missing |
| ambiguous_execution_lane | `classical_baseline_hopf_fibration` | `mixed_or_ambiguous` | `source_only_rerun_or_archive_decision` | execution_lane_conflict_requires_manual_review, linked_result_missing, result_contract_shape_missing, wizard_admission_missing |
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
| legacy_result_or_repair_needed | `sim_classical_leviathan_coalition_formation` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, load_bearing_tool_depth_missing, source_tool_integration_depth_missing, source_tool_manifest_missing |
| legacy_result_or_repair_needed | `sim_classical_sci_method_popper_refutation_count` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, load_bearing_tool_depth_missing, source_tool_integration_depth_missing, source_tool_manifest_missing |
| ambiguous_execution_lane, legacy_result_or_repair_needed | `sim_classical_szilard_maxwell_demon_coupled` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing, source_tool_integration_depth_missing |
| ambiguous_execution_lane, legacy_result_or_repair_needed | `sim_classical_weyl_chirality_extraction` | `classical` | `legacy_result_repair_or_quarantine` | classical_baseline_cannot_support_bridge_or_nonclassical_promotion, execution_lane_conflict_requires_manual_review, load_bearing_tool_depth_missing, source_tool_integration_depth_missing |

## First Cleanup Buckets

| bucket | stem | lane | engine types | role modes | public status |
| --- | --- | --- | --- | --- | --- |
| late_stage_blocked_decompose_before_rerun | `sim_classical_axis0_entropy_gradient_flow` | `classical` | none | unspecified | `exists` |
| late_stage_blocked_decompose_before_rerun | `sim_classical_axis6_action_handedness` | `classical` | none | unspecified | `exists` |
| late_stage_blocked_decompose_before_rerun | `sim_axis7_deep_test` | `unknown` | none | full_run_signal | `exists` |
| legacy_result_repair_or_quarantine | `sim_classical_bell_state_partial_trace` | `classical` | none | unspecified | `exists` |
| legacy_result_repair_or_quarantine | `sim_classical_fep_active_inference_step` | `classical` | none | unspecified | `exists` |
| legacy_result_repair_or_quarantine | `sim_classical_holodeck_carrier_shell_spectrum` | `classical` | none | unspecified | `exists` |
| repair_admission_result_link | `classical_baseline_cholesky_spd` | `classical` | none | unspecified | `exists` |
| repair_admission_result_link | `classical_baseline_gram_schmidt` | `classical` | none | unspecified | `exists` |
| repair_admission_result_link | `classical_baseline_graph_laplacian_spectrum` | `classical` | none | unspecified | `exists` |
| rerun_or_admission_candidate_review | `sim_clifford_holo_dirac_topology_variants` | `classical` | none | unspecified | `exists` |
| rerun_or_admission_candidate_review | `sim_contact_holo_weyl_topology_variants` | `classical` | none | unspecified | `exists` |
| rerun_or_admission_candidate_review | `sim_general_n_product_zero_theorem` | `unknown` | none | unspecified | `exists` |
| source_only_negative_or_graveyard_manifest_before_archive_decision | `axis0_bridge_owner_alignment_contract` | `semiclassical_bridge` | none | boundary_to_nonclassical_signal | `exists` |
| source_only_negative_or_graveyard_manifest_before_archive_decision | `axis0_bridge_owner_packet_surface` | `semiclassical_bridge` | none | boundary_to_nonclassical_signal | `exists` |
| source_only_negative_or_graveyard_manifest_before_archive_decision | `axis0_correlation_sim` | `nonclassical` | none | negative_space_or_graveyard_control | `exists` |
| source_only_rerun_or_archive_decision | `abiogenesis_sim` | `nonclassical` | none | unspecified | `exists` |
| source_only_rerun_or_archive_decision | `abiogenesis_v2_sim` | `nonclassical` | none | unspecified | `exists` |
| source_only_rerun_or_archive_decision | `alignment_sim` | `unknown` | none | full_run_signal | `exists` |
