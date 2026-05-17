# Formal Scout Readiness Index

Generated: `2026-05-17T06:09:56.472505+00:00`

Boundary: readiness index only. This does not rerun, admit, promote, or canonicalize formal scouts.

## Summary

- Result receipts indexed: `145`
- Source harnesses indexed: `146`
- Source harnesses without result receipt: `1`
- Validator pass: `128`
- Validator fail: `17`
- README indexed receipts: `78`
- README missing receipts: `67`
- Fresh-rerun mapping defects: `1`
- Fresh-rerun dual-source defects: `0`
- Backend policy violations: `0`
- Provider receipts indexed: `260`
- Provider receipt validator pass: `166`
- Provider receipt validator fail: `94`

## Readiness Status Counts

- `schema_ready`: 128
- `validator_failed`: 17

## Validation Error Counts

- `nearby_variants summary missing`: 17
- `why_not_v4_probes missing`: 16
- `graveyard_companions section missing`: 8
- `boundary section missing`: 7
- `positive section missing`: 3
- `one or more graveyard checks failed`: 2
- `claim_ceiling may overclaim`: 1
- `one or more positive checks failed`: 1

## Promotion Blocker Counts

- `formal_scout_noncanonical`: 145
- `fresh_rerun_not_performed`: 145
- `readme_index_missing`: 67
- `validator_failed`: 17
- `fresh_rerun_mapping_defect`: 1

## Tool Schema Key Styles

### TOOL_MANIFEST

- `upper`: 107
- `lower`: 31
- `both`: 7

### TOOL_INTEGRATION_DEPTH

- `upper`: 107
- `lower`: 31
- `both`: 7

## Provider Receipt Validation

- `pass`: 166
- `fail`: 94

### Provider Error Counts

- `missing repo_grounding`: 77
- `repo_grounding is not an object`: 77
- `invalid status`: 39
- `missing route`: 39
- `wrong schema`: 23
- `completed receipt missing proposal_text`: 15
- `evidence_allowed must be false`: 9
- `missing claim_ceiling`: 9
- `missing evidence_allowed`: 9
- `missing classification`: 7
- `missing promotion_allowed`: 7
- `missing status`: 7
- `promotion_allowed must be false`: 7
- `missing schema`: 6
- `missing provider`: 5

## Validator Failed Rows

| result | status | errors |
| --- | --- | --- |
| `system_v5/ops/formal_scouts/results/chiral_trajectory_persistent_homology_readout_feature_probe_results.json` | `validator_failed` | positive section missing, graveyard_companions section missing, boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/constraint_manifold_placement_neural_behavior_discrimination_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/e3nn_equivariant_constraint_manifold_geometric_feature_probe_results.json` | `validator_failed` | positive section missing, graveyard_companions section missing, boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/fe_asymmetry_pauli_generator_algebra_z3_derivation_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/fe_three_to_one_asymmetry_structural_origin_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/fresh_cycle_hysteresis_independence_falsifier_probe_results.json` | `validator_failed` | boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/full_thirteen_layer_tebd_native_evolution_strict_composition_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/late_stage_feature_only_classification_falsifier_probe_results.json` | `validator_failed` | graveyard_companions section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/late_stage_mutual_information_encoded_signal_probe_results.json` | `validator_failed` | graveyard_companions section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/late_stage_richer_readout_family_information_recovery_probe_results.json` | `validator_failed` | graveyard_companions section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/loop_A_reversibility_attractor_vs_path_geometry_falsifier_probe_results.json` | `validator_failed` | boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/non_abelian_schedule_order_commutator_probe_results.json` | `validator_failed` | graveyard_companions section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/paired_chiral_bipartite_logarithmic_negativity_coupling_probe_results.json` | `validator_failed` | claim_ceiling may overclaim, graveyard_companions section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe_results.json` | `validator_failed` | boundary section missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/source_native_engine_transition_phase_boundary_path_fep_probe_results.json` | `validator_failed` | boundary section missing, why_not_v4_probes missing, nearby_variants summary missing, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/xgi_hypergraph_multi_layer_coupling_centrality_probe_results.json` | `validator_failed` | positive section missing, graveyard_companions section missing, boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |

## Fresh-Rerun Mapping Defects

| result | validator expected source | actual source |
| --- | --- | --- |
| `system_v5/ops/formal_scouts/results/sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe_results.json` | `system_v5/ops/formal_scouts/sim_sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe.py` | `system_v5/ops/formal_scouts/sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe.py` |

## Backend Policy Violations

| result | source | violations |
| --- | --- | --- |
| - | - | - |

## README Missing Samples

- `system_v5/ops/formal_scouts/results/chiral_trajectory_persistent_homology_readout_feature_probe_results.json`
- `system_v5/ops/formal_scouts/results/closed_loop_holonomy_hysteresis_falsifier_probe_results.json`
- `system_v5/ops/formal_scouts/results/constraint_manifold_delta_neural_readout_probe_results.json`
- `system_v5/ops/formal_scouts/results/constraint_manifold_discrete_degrees_of_freedom_enumeration_probe_results.json`
- `system_v5/ops/formal_scouts/results/constraint_manifold_layer_causal_responsibility_matrix_probe_results.json`
- `system_v5/ops/formal_scouts/results/constraint_manifold_placement_neural_behavior_discrimination_probe_results.json`
- `system_v5/ops/formal_scouts/results/constraint_manifold_qit_engine_work_execution_probe_results.json`
- `system_v5/ops/formal_scouts/results/discrete_dof_topological_obstruction_interpolation_probe_results.json`
- `system_v5/ops/formal_scouts/results/e3nn_equivariant_constraint_manifold_geometric_feature_probe_results.json`
- `system_v5/ops/formal_scouts/results/eight_qubit_mps_channel_order_graph_leakage_pyg_pytorch_opt_einsum_z3_probe_results.json`
- `system_v5/ops/formal_scouts/results/eight_qubit_mps_entropy_readout_layer_constraint_probe_results.json`
- `system_v5/ops/formal_scouts/results/engine_core_autograd_severance_contract_probe_results.json`
- `system_v5/ops/formal_scouts/results/engine_operator_slot_alphabet_contract_probe_results.json`
- `system_v5/ops/formal_scouts/results/fe_asymmetry_pauli_generator_algebra_z3_derivation_probe_results.json`
- `system_v5/ops/formal_scouts/results/fe_three_to_one_asymmetry_structural_origin_probe_results.json`
- `system_v5/ops/formal_scouts/results/finite_density_hopf_spinor_clifford_channel_structure_reduction_order_probe_results.json`
- `system_v5/ops/formal_scouts/results/finite_spinor_tensor_network_channel_order_noncommutation_probe_results.json`
- `system_v5/ops/formal_scouts/results/fresh_cycle_hysteresis_independence_falsifier_probe_results.json`
- `system_v5/ops/formal_scouts/results/full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe_results.json`
- `system_v5/ops/formal_scouts/results/full_thirteen_layer_tebd_native_evolution_strict_composition_probe_results.json`
- `system_v5/ops/formal_scouts/results/high_n_mps_engine_boundary_path_fep_transport_probe_results.json`
- `system_v5/ops/formal_scouts/results/holographic_boundary_path_ensemble_axis0_fep_selection_probe_results.json`
- `system_v5/ops/formal_scouts/results/late_stage_feature_only_classification_falsifier_probe_results.json`
- `system_v5/ops/formal_scouts/results/late_stage_mutual_information_encoded_signal_probe_results.json`
- `system_v5/ops/formal_scouts/results/late_stage_richer_readout_family_information_recovery_probe_results.json`
- `system_v5/ops/formal_scouts/results/lirpa_peps3d_size_normalized_environment_scaling_probe_results.json`
- `system_v5/ops/formal_scouts/results/loop_A_reversibility_attractor_vs_path_geometry_falsifier_probe_results.json`
- `system_v5/ops/formal_scouts/results/mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_mps_reservoir_12_16_24_32_scaling_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_dense_order_holonomy_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_digits_6q_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_global_structure_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_grok_task_replication_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_meanfield_ablation_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_temporal_ablation_probe_results.json`
- `system_v5/ops/formal_scouts/results/multiqubit_reservoir_static_kernel_esn_baseline_probe_results.json`
- `system_v5/ops/formal_scouts/results/non_abelian_schedule_order_commutator_probe_results.json`
- `system_v5/ops/formal_scouts/results/operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe_results.json`
- `system_v5/ops/formal_scouts/results/paired_chiral_bipartite_logarithmic_negativity_coupling_probe_results.json`
- `system_v5/ops/formal_scouts/results/paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe_results.json`
- `system_v5/ops/formal_scouts/results/peps3d_campaign_claim_ceiling_status_audit_probe_results.json`
- `system_v5/ops/formal_scouts/results/probe_family_discrimination_chi_transport_8_16_32_probe_results.json`
- `system_v5/ops/formal_scouts/results/qit_engine_dynamics_required_work_discrimination_probe_results.json`
- `system_v5/ops/formal_scouts/results/qit_engine_probe_family_reconciliation_intersection_probe_results.json`
- `system_v5/ops/formal_scouts/results/qit_engines_perform_classification_task_with_trainable_readout_probe_results.json`
- `system_v5/ops/formal_scouts/results/si_te_te_si_ni_te_te_ni_signed_gradient_weyl_terrain_substages_probe_results.json`
- `system_v5/ops/formal_scouts/results/sim_four_topology_behavior_class_scaling_eight_and_twelve_qubit_probe_results.json`
- `system_v5/ops/formal_scouts/results/source_native_active_inference_strategy_policy_probe_results.json`
- `system_v5/ops/formal_scouts/results/source_native_engine_boundary_path_fep_reconstruction_probe_results.json`
- `system_v5/ops/formal_scouts/results/source_native_engine_transition_phase_boundary_path_fep_probe_results.json`
