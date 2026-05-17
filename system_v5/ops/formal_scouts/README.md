# Formal-Scout Geometric Constraint Manifold Work

Status: exploratory, noncanonical

This directory is the clean middle layer between informal provider proposals and
canonical `system_v4/probes` sims.

`system_v4/probes` is the reference corpus for this work, not the exploratory
write surface. New manifold exploration stays here unless a later promotion
manifest explicitly moves a hardened sim.

## Rules

- Harnesses may import existing formal legos.
- Harnesses must write result receipts under `results/`.
- Harnesses must set `classification: formal_scout`.
- Harnesses must set `promotion_allowed: false`.
- Harnesses must include nearby graveyards.
- Names must describe the math being simulated.

## Current Harnesses

| Harness | Result | Readout | Ceiling |
|---|---|---|---|
| `sim_nested_finite_geometry_holonomy_noncommutation_probe.py` | `results/nested_finite_geometry_holonomy_noncommutation_probe_results.json` | nested density/Hopf/holonomy/transport tower | formal scout only |
| `sim_entropy_reduction_before_hopf_projection_order_probe.py` | `results/entropy_reduction_before_hopf_projection_order_probe_results.json` | entropy-filtered finite density family before Hopf projection readout | formal scout only |
| `sim_su2_unit_quaternion_hopf_holonomy_order_probe.py` | `results/su2_unit_quaternion_hopf_holonomy_order_probe_results.json` | SU2 unit-quaternion transport order plus Hopf connection loop readouts | formal scout only |
| `sim_entropy_family_admission_matrix_for_geometry_outputs_and_density_coercions_probe.py` | `results/entropy_family_admission_matrix_for_geometry_outputs_and_density_coercions_probe_results.json` | entropy-family admission over geometry outputs and density coercions | formal scout only |
| `sim_ordered_geometry_layer_transition_signed_entropy_depth_probe.py` | `results/ordered_geometry_layer_transition_signed_entropy_depth_probe_results.json` | ordered layer transition depth for mutual, signed conditional, and coherent information | formal scout only |
| `sim_eight_qubit_dynamic_geometry_signed_entropy_cut_depth_probe.py` | `results/eight_qubit_dynamic_geometry_signed_entropy_cut_depth_probe_results.json` | eight-qubit dynamic geometry parameter with signed entropy across cut depths | formal scout only |
| `sim_nested_geometry_tower_dependency_order_probe.py` | `results/nested_geometry_tower_dependency_order_probe_results.json` | candidate nested geometry tower dependency order with concrete witnesses | formal scout only |
| `sim_pytorch_neural_network_dynamic_geometry_coherent_information_regression_probe.py` | `results/pytorch_neural_network_dynamic_geometry_coherent_information_regression_probe_results.json` | PyTorch neural network learns coherent-information readout surface | formal scout only |
| `sim_first_order_gradient_direction_variants_on_signed_entropy_probe.py` | `results/first_order_gradient_direction_variants_on_signed_entropy_probe_results.json` | first-order gradient direction variants on signed entropy | formal scout only |
| `sim_eight_qubit_xx_chain_dynamic_geometry_signed_entropy_threshold_probe.py` | `results/eight_qubit_xx_chain_dynamic_geometry_signed_entropy_threshold_probe_results.json` | eight-qubit XX-chain signed entropy threshold across all cuts | formal scout only |
| `sim_pauli_correlated_topology_flux_operator_channel_tensor_network_probe.py` | `results/pauli_correlated_topology_flux_operator_channel_tensor_network_probe_results.json` | Pauli-correlated topology-flux channels crossed with four operator channels on an eight-qubit tensor network | formal scout only |
| `sim_variable_qubit_topology_flux_channel_order_entropy_scaling_probe.py` | `results/variable_qubit_topology_flux_channel_order_entropy_scaling_probe_results.json` | two-to-eight qubit scaling audit for topology-flux channel-order gaps and signed entropy | formal scout only |
| `sim_constraint_survivor_probe_quotient_order_dependence_probe.py` | `results/constraint_survivor_probe_quotient_order_dependence_probe_results.json` | finite candidate density assemblies constrained into survivor sets and quotiented by probe indistinguishability | formal scout only |
| `sim_hard_constraint_survivor_probe_quotient_pruning_order_probe.py` | `results/hard_constraint_survivor_probe_quotient_pruning_order_probe_results.json` | hard admissibility predicates prune finite density candidates before probe indistinguishability quotienting | formal scout only |
| `sim_hard_constraint_threshold_sweep_probe_quotient_stability_probe.py` | `results/hard_constraint_threshold_sweep_probe_quotient_stability_probe_results.json` | hard admissibility threshold sweep over survivor counts and probe quotient stability | formal scout only |
| `sim_density_metric_geometry_survivor_quotient_persistence_probe.py` | `results/density_metric_geometry_survivor_quotient_persistence_probe_results.json` | density-matrix metric geometries compared as hard constraint layers with survivor quotients and Rips persistence | formal scout only |
| `sim_special_holonomy_form_constraint_survivor_quotient_probe.py` | `results/special_holonomy_form_constraint_survivor_quotient_probe_results.json` | finite SU3-like, G2-like, and Spin7-like exterior-form constraints compared with generic controls by survivor quotients | formal scout only |
| `sim_special_form_signed_permutation_survivor_quotient_probe.py` | `results/special_form_signed_permutation_survivor_quotient_probe_results.json` | finite signed-permutation frame actions preserving SU3-like, G2-like, Spin7-like, and generic exterior forms | formal scout only |
| `sim_special_form_density_metric_coupled_survivor_quotient_probe.py` | `results/special_form_density_metric_coupled_survivor_quotient_probe_results.json` | sampled special-form signed frame actions projected into density channels and compared by density-metric survivor quotients | formal scout only |
| `sim_future_possibility_past_correlation_shell_direction_survivor_quotient_probe.py` | `results/future_possibility_past_correlation_shell_direction_survivor_quotient_probe_results.json` | one finite shell with future-possibility expansion and past-correlation binding as opposite dynamic directions | formal scout only |
| `sim_three_dimensional_shell_flux_inverse_square_geometry_probe.py` | `results/three_dimensional_shell_flux_inverse_square_geometry_probe_results.json` | shell-spread flux slopes across dimensions with aligned/off-axis anisotropy and no-spread controls | formal scout only |
| `sim_density_spinor_hopf_shell_graph_coherent_information_coupling_probe.py` | `results/density_spinor_hopf_shell_graph_coherent_information_coupling_probe_results.json` | finite density states carried by spinors, Hopf-projected to shell graph weights, then quotiented by coherent-information survivor readouts | formal scout only |
| `sim_spinor_shell_coherent_information_locality_preserving_rank3_control_probe.py` | `results/spinor_shell_coherent_information_locality_preserving_rank3_control_probe_results.json` | coherent-information and conditional-entropy orbit quotient for dynamic-shell gamma5 sequences against shell-independent locality-preserving rank-3 split-jump controls | formal scout only |
| `sim_spinor_shell_coherent_information_time_dependent_rank3_equivalence_kill_probe.py` | `results/spinor_shell_coherent_information_time_dependent_rank3_equivalence_kill_probe_results.json` | kill-boundary scout showing shell-independent time-dependent locality-preserving rank-3 split-jump sequences exactly reproduce the dynamic-shell gamma5 coherent-information orbit when per-step rates are allowed to match | formal scout only |
| `sim_dynamic_shell_rate_sequence_parameter_compression_probe.py` | `results/dynamic_shell_rate_sequence_parameter_compression_probe_results.json` | dynamic shell graph mean/std features compress the six-step gamma5 rank-3 split-jump channel rate sequence while random and permuted rate controls fail | formal scout only |
| `sim_gamma5_offdiagonal_coherence_persistence_rate_compression_probe.py` | `results/gamma5_offdiagonal_coherence_persistence_rate_compression_probe_results.json` | kill-boundary scout showing the current coarse gamma5 off-diagonal point-cloud persistence signature collapses under random, permuted, constant-mean, and same-rate controls | formal scout only |
| `sim_boundary_conditional_expectation_area_law_entropy_scaling_probe.py` | `results/boundary_conditional_expectation_area_law_entropy_scaling_probe_results.json` | finite conditional expectation from cubic bulk density algebra to boundary-supported density; boundary support scales near area while bulk support scales as volume | formal scout only |
| `sim_boundary_projected_gamma5_chirality_channel_trace_distance_probe.py` | `results/boundary_projected_gamma5_chirality_channel_trace_distance_probe_results.json` | finite boundary conditional expectation composed with gamma5 chirality-asymmetric CPTP channels and read by trace-distance orbits; partial survivor rows only | formal scout only |
| `sim_boundary_projected_gamma5_chirality_channel_choi_rank_probe.py` | `results/boundary_projected_gamma5_chirality_channel_choi_rank_probe_results.json` | effective Choi matrix for finite boundary-projected gamma5 chirality-asymmetric channel sequence; target rank 9 resists symmetric, equal-rate, and random-boundary controls | formal scout only |
| `sim_boundary_projected_gamma5_chirality_channel_coherent_information_probe.py` | `results/boundary_projected_gamma5_chirality_channel_coherent_information_probe_results.json` | finite boundary conditional expectation composed with gamma5 chirality-asymmetric CPTP channels and read by coherent-information and conditional-entropy orbits; four-qubit scout only | formal scout only |
| `sim_eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe.py` | `results/eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe_results.json` | eight-qubit finite boundary conditional expectation composed with gamma5 chirality-asymmetric CPTP channels and read by coherent-information and conditional-entropy orbits across a 4\|4 split | formal scout only |
| `sim_eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe.py` | `results/eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe_results.json` | eight-qubit boundary-projected gamma5 channel sequences compared by Rips persistence signatures of mutual-information time-step distances; partial survivor rows only, with time-order collisions recorded | formal scout only |
| `sim_eight_qubit_dynamic_shell_graph_tensor_network_entropy_coupling_probe.py` | `results/eight_qubit_dynamic_shell_graph_tensor_network_entropy_coupling_probe_results.json` | eight-qubit finite tensor state coupled to anisotropic dynamic shell graph generators and read by conditional entropy plus coherent information | formal scout only |
| `sim_integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe.py` | `results/integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe_results.json` | integrated nested geometry tower, source-native Weyl terrain histories, support G-structure scaffold, topology witnesses, and eight-qubit dynamic shell tensor-network readouts | formal scout only |
| `sim_exceptional_jordan_octonion_derivation_dimension_chain_probe.py` | `results/exceptional_jordan_octonion_derivation_dimension_chain_probe_results.json` | 27-dimensional exceptional Jordan algebra over octonions with derivation and idempotent-stabilizer null-space constraints | formal scout only |
| `sim_chirality_asymmetric_channel_coherent_information_novelty_killer_probe.py` | `results/chirality_asymmetric_channel_coherent_information_novelty_killer_probe_results.json` | novelty-killer comparing chirality-symmetric shell-direction channels to textbook CPTP channels and chirality-asymmetric CPTP channels by coherent information | formal scout only |
| `sim_hopf_shell_chirality_asymmetric_cptp_entropy_coupling_probe.py` | `results/hopf_shell_chirality_asymmetric_cptp_entropy_coupling_probe_results.json` | four-qubit Hopf shell graph weights driving chirality-asymmetric CPTP channel blocks and signed entropy readouts | formal scout only |
| `sim_eight_qubit_dynamic_shell_chirality_asymmetric_cptp_entropy_coupling_probe.py` | `results/eight_qubit_dynamic_shell_chirality_asymmetric_cptp_entropy_coupling_probe_results.json` | eight-qubit dynamic shell graph tensor evolution followed by four-component gamma5 chirality-asymmetric CPTP channel blocks; effective-gamma sweep kills this readout as a structural novelty witness | formal scout only |
| `sim_eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe.py` | `results/eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe_results.json` | eight-qubit dynamic shell gamma5 chirality-asymmetric CPTP sequences quotiented by off-diagonal trace-norm orbit signatures; dynamic beats static but not uniform shell control | formal scout only |
| `sim_gamma5_offdiagonal_coherence_trace_orbit_effective_channel_probe.py` | `results/gamma5_offdiagonal_coherence_trace_orbit_effective_channel_probe_results.json` | four-qubit gamma5 block off-diagonal coherence trace-norm orbit under chirality-asymmetric CPTP channels with symmetric effective-channel fit control | formal scout only |
| `sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe.py` | `results/gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe_results.json` | finite family of four-qubit gamma5 block off-diagonal coherence trace-norm orbits quotiented into survivor classes after symmetric effective-gamma controls | formal scout only |
| `sim_gamma5_offdiagonal_coherence_trace_orbit_threshold_sweep_probe.py` | `results/gamma5_offdiagonal_coherence_trace_orbit_threshold_sweep_probe_results.json` | threshold sweep over four-qubit gamma5 off-diagonal coherence trace-orbit survivor quotient classes after symmetric effective-gamma controls | formal scout only |
| `sim_gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel_probe.py` | `results/gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel_probe_results.json` | kill-boundary scout showing shell-independent locality-preserving rank-3 split-jump channels collapse the dynamic-shell gamma5 off-diagonal trace-orbit residual quotient | formal scout only |
| `sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe.py` | `results/gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe_results.json` | four-component gamma5 chirality-asymmetric CPTP channel compared to the one-parameter symmetric effective-gamma channel family by Choi trace distance and Stinespring-isometry projector distance | formal scout only |
| `sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe.py` | `results/dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe_results.json` | dynamic shell graph weights coupled to gamma5 chirality-asymmetric CPTP channel sequences and quotiented by off-diagonal trace-norm orbit signatures with Choi-distance controls | formal scout only |
| `sim_gamma5_chirality_asymmetric_cptp_arbitrary_kraus_equivalence_kill_probe.py` | `results/gamma5_chirality_asymmetric_cptp_arbitrary_kraus_equivalence_kill_probe_results.json` | kill-boundary scout showing unrestricted arbitrary-Kraus CPTP exactly represents the gamma5 chirality-asymmetric channel while the one-parameter symmetric effective-gamma family does not | formal scout only |
| `sim_gamma5_chirality_asymmetric_cptp_matched_rank_split_jump_channel_probe.py` | `results/gamma5_chirality_asymmetric_cptp_matched_rank_split_jump_channel_probe_results.json` | matched-rank equal-rate split-jump CPTP family compared to gamma5 chirality-asymmetric CPTP target and lower-rank combined symmetric effective-gamma family by Choi and Stinespring distances | formal scout only |
| `sim_left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe.py` | `results/left_right_weyl_density_terrain_loop_placement_mirror_non_equivalence_probe_results.json` | source-native left/right Weyl density states with signed Hamiltonians, opposite ladder dissipators, terrain-law families, and fiber/base-lift Hopf loop placements | formal scout only |
| `sim_left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe.py` | `results/left_right_weyl_density_hopf_loop_shell_graph_persistence_coupling_probe_results.json` | source-native left/right Weyl density terrain-loop histories mapped into finite shell graph filtrations and H0 persistence signatures, with mean-only and permuted controls kept as live boundaries | formal scout only |
| `sim_left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe.py` | `results/left_right_weyl_density_terrain_loop_stage_subcycle_execution_probe_results.json` | source-native left/right Weyl density operating spaces executed through two valid four-stage traversals and four operator substages per macro-stage | formal scout only |
| `sim_strong_geometric_flux_nested_hopf_torus_weyl_density_probe.py` | `results/strong_geometric_flux_nested_hopf_torus_weyl_density_probe_results.json` | derived strong geometric flux from source-native Weyl density stage deltas nested on Hopf-torus loop area, holonomy, shell spread, and tensor transport | formal scout only |
| `sim_two_chiral_operating_spaces_thirty_two_stage_manifold_constrained_dynamic_tensor_network_probe.py` | `results/two_chiral_operating_spaces_thirty_two_stage_manifold_constrained_dynamic_tensor_network_probe_results.json` | two source-native chiral operating spaces executing 32 manifold-constrained stages each on a 12-qubit dynamic tensor-network carrier | formal scout only |
| `sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py` | `results/four_topology_behavior_class_chiral_loop_operator_separation_probe_results.json` | four topology classes with paired chiral realizations, inner/outer loop placements, ordered operator pairs, and signed operator directions tested as behavior-signature classes | formal scout only |
| `sim_entropy_gradient_metric_connection_deformation_probe.py` | `results/entropy_gradient_metric_connection_deformation_probe_results.json` | entropy gradient used as a deformation field over finite metric scale, connection strength, and Hopf-loop geometry, with frozen and readout-only controls | formal scout only |
| `sim_entropy_gradient_curvature_torsion_deformation_probe.py` | `results/entropy_gradient_curvature_torsion_deformation_probe_results.json` | entropy-gradient flow over finite metric, shear, twist, curvature scalar, and torsion-style antisymmetric-connection proxy with flat/frozen/random controls | formal scout only |
| `sim_quimb_cotengra_tensor_network_geometry_contraction_probe.py` | `results/quimb_cotengra_tensor_network_geometry_contraction_probe_results.json` | quimb MPS topology entropy readouts and cotengra contraction-tree search admitted as load-bearing tensor-network tools for later dynamic-geometry integration | formal scout only |
| `sim_topology_entropy_deformation_tensor_network_coupling_probe.py` | `results/topology_entropy_deformation_tensor_network_coupling_probe_results.json` | four topology classes coupled to entropy-gradient deformation, quimb MPS evolution, and cotengra geometry-shaped contraction trees with frozen and collapsed controls | formal scout only |
| `sim_mps_peps_sheet_topology_entropy_deformation_comparison_probe.py` | `results/mps_peps_sheet_topology_entropy_deformation_comparison_probe_results.json` | one-dimensional MPS chain and two-dimensional PEPS sheet carriers compared under the same topology-class entropy-deformation schedule | formal scout only |
| `sim_mps_peps_peps3d_entropy_deformation_volume_comparison_probe.py` | `results/mps_peps_peps3d_entropy_deformation_volume_comparison_probe_results.json` | one-dimensional MPS chain, two-dimensional PEPS sheet, and three-dimensional PEPS3D volume carriers compared under one entropy-gradient deformation schedule | formal scout only |
| `sim_constraint_manifold_multitool_entropy_geometry_carrier_integration_probe.py` | `results/constraint_manifold_multitool_entropy_geometry_carrier_integration_probe_results.json` | multitool finite manifold integration coupling density updates, entropy-gradient geometry flow, tensor carriers, graph/hypergraph/simplicial topology, persistence, SMT, equivariant inventory, and graph-neural readout | formal scout only |
| `sim_source_chiral_density_multicarrier_multitool_manifold_execution_probe.py` | `results/source_chiral_density_multicarrier_multitool_manifold_execution_probe_results.json` | source-native left/right density histories drive multicarrier MPS/PEPS/PEPS3D multitool manifold execution with topology, persistence, symbolic, SMT, metric, contraction, equivariant, and graph-neural readouts | formal scout only |
| `sim_long_horizon_source_multicarrier_holonomy_boundary_entropy_probe.py` | `results/long_horizon_source_multicarrier_holonomy_boundary_entropy_probe_results.json` | long-horizon source-native multicarrier manifold run with H0/H1 persistence, closed-loop holonomy/hysteresis, shell/boundary entropy, held-out neural controls, SMT, metric, and contraction readouts | formal scout only |
| `sim_operational_manifest_source_downstream_quarantine_probe.py` | `results/operational_manifest_source_downstream_quarantine_probe_results.json` | operational evidence manifest verifying source-native, downstream-on-source, and proxy-quarantined receipt surfaces while keeping gamma/proxy receipts out of source-native proof | formal scout only |
| `sim_integrated_constraint_manifold_suite_fresh_rerun_probe.py` | `results/integrated_constraint_manifold_suite_fresh_rerun_probe_results.json` | ordered fresh-rerun harness for the integrated source-native, tensor-network, multicarrier, macro-sim/FEP/Axis0/Holodeck/LiRPA, long-horizon, and quarantine-manifest formal-scout suite | formal scout only |
| `sim_source_chiral_entropy_feedback_sixty_four_microstep_execution_probe.py` | `results/source_chiral_entropy_feedback_sixty_four_microstep_execution_probe_results.json` | source-native 64-microstep execution with entropy-gradient feedback between geometry and stage dynamics, all 8 operator-sign pairs per chiral sheet, persistence readout, and frozen/wrong-sign/collapsed-sign controls | formal scout only |
| `sim_nested_constraint_manifold_operational_handle_support_probe.py` | `results/nested_constraint_manifold_operational_handle_support_probe_results.json` | manifold-first 13-layer support relation for seven downstream operational handles, with hypergraph/simplicial/persistence/message-pass/SMT checks and collapse-to-Weyl/one-layer/downstream-only graveyards | formal scout only |
| `sim_nested_constraint_manifold_operational_assembly_tensor_network_probe.py` | `results/nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json` | single 64-step operational assembly where all 13 nested manifold layers constrain and deform an 8-site quimb MPS, using cotengra, topology, geometry, symbolic, SMT, and layer-removal graveyards as load-bearing checks | formal scout only |
| `sim_source_chiral_seven_control_sixty_four_microstep_execution_probe.py` | `results/source_chiral_seven_control_sixty_four_microstep_execution_probe_results.json` | conditional downstream 64-microstep execution with seven executable handles; useful only after manifold-support or operational-assembly receipts, and not standalone axis/manifold evidence | formal scout only |
| `sim_paired_chiral_seven_control_joint_bipartite_execution_order_probe.py` | `results/paired_chiral_seven_control_joint_bipartite_execution_order_probe_results.json` | conditional downstream joint 4x4 paired-chiral readout with mutual information, logarithmic negativity, order sensitivity, persistence, and controls; depends on manifold-first support plus seven-handle source receipt | formal scout only |

## Recent Source-Native Macro-Sim Repair Scouts

| Harness | Result | Readout | Ceiling |
|---|---|---|---|
| `sim_macro_sim_stage_record_science_method_contract_probe.py` | `results/macro_sim_stage_record_science_method_contract_probe_results.json` | EngineCore stage records expose executable science-method/FEP fields and matched no-manifold controls | formal scout only |
| `sim_macro_sim_axis0_plural_stage_candidate_router_probe.py` | `results/macro_sim_axis0_plural_stage_candidate_router_probe_results.json` | plural Axis0 candidate routing over FEP-gradient polarity, path entropy, correlation-diversity derivative, finite boundary/interior reconstruction, and finite many-futures policy-tree scoring | formal scout only |
| `sim_source_native_holodeck_hash_memory_placeholder_probe.py` | `results/source_native_holodeck_hash_memory_placeholder_probe_results.json` | predictive-model plus contextual semantic-hash recall placeholder with hash-only and wrong-model controls | formal scout only |
| `sim_source_native_multicarrier_subdense_environment_contraction_probe.py` | `results/source_native_multicarrier_subdense_environment_contraction_probe_results.json` | MPS/PEPS/PEPS3D local environment readouts consuming stage, FEP, Axis0, and Holodeck-memory signals | formal scout only |
| `sim_world_model_repo_admission_gap_adapter_probe.py` | `results/world_model_repo_admission_gap_adapter_probe_results.json` | external world-model/neural repo admission gate using Gap -> Repo -> Adapter -> Consumption Test -> Control | formal scout only |
| `sim_auto_lirpa_stage_policy_bound_consumption_probe.py` | `results/auto_lirpa_stage_policy_bound_consumption_probe_results.json` | downstream auto_LiRPA BoundedModule interval check over source-native stage/FEP/Axis0/Holodeck policy features | formal scout only |
| `sim_auto_lirpa_trained_stage_policy_adapter_bound_probe.py` | `results/auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json` | trained source-native stage-policy adapter with auto_LiRPA interval bounds checked against brute-force perturbation samples | formal scout only |
| `sim_lirpa_policy_bound_gated_multicarrier_environment_probe.py` | `results/lirpa_policy_bound_gated_multicarrier_environment_probe_results.json` | trained LiRPA policy-bound gates modulate MPS/PEPS/PEPS3D local environment updates against flat, shuffled, and zero-gate controls | formal scout only |
| `sim_lirpa_policy_bound_variable_qubit_scaling_probe.py` | `results/lirpa_policy_bound_variable_qubit_scaling_probe_results.json` | LiRPA policy-bound gate consumption across variable MPS/PEPS/PEPS3D site counts, with local-sensitive PEPS3D64 scaling admitted and compressed-summary attenuation retained as a blocker | formal scout only |

## Next Queue

| Priority | Candidate | Purpose | Status |
|---|---|---|---|
| 1 | `sim_entropy_reduction_before_hopf_projection_order_probe.py` | test whether entropy filtering before projection changes finite survivor/readout structure | passing scout |
| 2 | `sim_su2_unit_quaternion_hopf_holonomy_order_probe.py` | test non-Abelian/SU(2)-style transport against U(1) controls | passing scout |
| 3 | `sim_spinor_clifford_pauli_projection_order_probe.py` | test spinor-to-Clifford-to-Pauli layer ordering with adjacent controls | proposed |
| 4 | `sim_topology_cycle_hopf_projection_order_probe.py` | test finite topology readouts around Hopf projection and path order | proposed |

## Provider Split

Grok/Gemini may propose alternatives and attacks. Their output is not evidence
until Codex maps it to real repo callables and a formal-scout receipt.

Latest provider receipts:
`provider_receipts/20260515T195653Z_gemini_topology_entropy_tensor_network_provider_review.json`
and
`provider_receipts/20260515T195653Z_grok_xai_topology_entropy_tensor_network_provider_review.json`.

Machine-readable provider receipts live under `provider_receipts/`.

## Validation

Run:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py`

Fresh rerun plus receipt validation:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun`

Name lint:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/lint_formal_scout_names.py`

Provider receipts:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/ops/formal_scouts/validate_provider_receipts.py`
