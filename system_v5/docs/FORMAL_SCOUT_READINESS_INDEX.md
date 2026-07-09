# Formal Scout Readiness Index

Generated: `2026-07-01T03:20:29.975866+00:00`

Boundary: readiness index only. This does not rerun, admit, promote, or canonicalize formal scouts.

## Summary

- Result receipts indexed: `558`
- Source harnesses indexed: `495`
- Source harnesses without result receipt: `102`
- Validator pass: `237`
- Formal-scout validator fail: `103`
- Preserved validator-red rows: `12`
- Actionable validator-red rows: `91`
- Non-formal boundary rows: `220`
- README indexed receipts: `325`
- README missing receipts: `233`
- README explicit-status mismatches: `47`
- Fresh-rerun mapping defects: `0`
- Fresh-rerun dual-source defects: `0`
- Backend policy violations: `0`
- Provider receipts indexed: `48`
- Provider JSON sidecars skipped: `0`
- Provider receipt validator pass: `48`
- Provider receipt validator fail: `0`
- Provider strict-live validator pass: `46`
- Provider strict-live validator fail: `2`

## Readiness Status Counts

- `schema_ready`: 235
- `non_formal_boundary`: 220
- `validator_failed`: 103

## Validation Error Counts

- `evidence_level is not tool_capability/tool_lego_fit/consumer_gate`: 218
- `tool_claim/tool_claims missing`: 218
- `blocked_downstream_consumers missing`: 203
- `engine_contract missing`: 202
- `source_sha256 missing`: 160
- `summary missing`: 159
- `one or more positive checks failed`: 96
- `claim_ceiling missing`: 61
- `one or more graveyard checks failed`: 39
- `nearby_variants did not all pass`: 35
- `blockers present`: 32
- `claim_ceiling may overclaim`: 21
- `one or more boundary checks failed`: 16
- `source_path missing`: 15
- `all_pass is not true`: 12
- `nearby_variants summary missing`: 5
- `graveyard_companions section missing`: 2
- `positive section missing`: 2
- `boundary section missing`: 1
- `formal_admission_allowed is not false`: 1
- `why_not_v4_probes missing`: 1

## Validator Failure Kind Counts

- `uncategorized_validator_failure`: 91
- `stale_noncovering_engine_core_finite_boundary_debt`: 10
- `overclaim_risk_failed_probe`: 2

## Validator Failure Handling Counts

- `manual_triage_required`: 91
- `preserve_red_nonclearance`: 10
- `preserve_failed_probe_or_rerun_revised_design`: 2

## Actionable vs Preserved Red Rows

- Preserved red rows: `12`
- Actionable red rows: `91`

Preserved red rows are intentionally retained as negative, nonclearance, or overclaim-boundary evidence. They are not green proofs and not current readiness-repair debt. Actionable red rows require new repair, rerun, or manual triage before closeout.

## Promotion Blocker Counts

- `formal_scout_noncanonical`: 558
- `fresh_rerun_not_performed`: 558
- `readme_index_missing`: 233
- `classification_not_formal_scout`: 220
- `non_formal_boundary`: 220
- `validator_failed`: 103

## Pass Source Counts

- `all_pass`: 462
- `summary.all_pass`: 56
- `derived_formal_scout_sections`: 34
- `missing`: 6

## Tool Schema Key Styles

### TOOL_MANIFEST

- `upper`: 309
- `both`: 177
- `lower`: 57
- `missing`: 15

### TOOL_INTEGRATION_DEPTH

- `upper`: 310
- `both`: 176
- `lower`: 57
- `missing`: 15

## Provider Receipt Validation

- `pass`: 48
- `fail`: 0

### Strict-Live Provider Provenance

Normal provider validation is schema/proposal-boundary validation. Strict-live validation is the provenance check for completed live-provider receipts.
- `pass`: 46
- `fail`: 2

### Strict-Live Provider Error Counts

- `strict-live completed provider receipt missing raw_response or live_api_proof`: 2

## Validator Failed Rows

| result | failure kind | handling | resolution surface | errors |
| --- | --- | --- | --- | --- |
| `system_v5/ops/formal_scouts/results/active_policy_online_vmp_margin_closure_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/attractor_basin_success_criteria_receipt_classifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/attractor_basin_tmp_engine_v2_candidate_execution_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/attractor_basin_tmp_engine_v2_full_wave_execution_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/attractor_basin_tmp_engine_v2_receipt_resolution_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/attractor_basin_tmp_engine_v2_timeout_rerun_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/attractor_basin_tmp_grok_sidequest_adoption_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/attractor_basin_tmp_to_source_native_adoption_bridge_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/auto_lirpa_stage_policy_bound_consumption_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/axis0_holographic_boundary_branch_closure_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/axis0_path_entropy_branch_closure_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/axis0_plural_candidate_multicarrier_drive_controls_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/constraint_manifold_terrain_lindblad_composition_bridge_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/deep_basin_evidence_aggregator_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/engine_core_boundary_row_triage_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_dynamic_boundary_port_demote_classifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_axis0_fep_gradient_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_constraint_manifold_delta_neural_readout_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_active_inference_strategy_policy_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_fep_pomdp_policy_tree_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_holodeck_hash_memory_placeholder_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_hopf_fep_igt_chirality_prediction_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_multicarrier_subdense_environment_contraction_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_peps3d_32_64_site_capacity_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_peps3d_48_site_regime_crossing_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_finite_boundary_source_native_peps3d_52_56_60_site_regime_ladder_receipt_probe_results.json` | `stale_noncovering_engine_core_finite_boundary_debt` | `preserve_red_nonclearance` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/engine_core_importer_boundary_classifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/entropy_reduction_before_hopf_projection_order_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | positive section missing, graveyard_companions section missing, nearby_variants summary missing, one or more boundary checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/holodeck_basin_grade_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/holodeck_core_prediction_memory_seed_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/holodeck_qit_spinor_memory_adapter_seed_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/lewm_adaLN_branch_dynamics_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/lirpa_peps3d_size_normalized_environment_scaling_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/lirpa_policy_bound_gated_multicarrier_environment_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/lirpa_policy_bound_variable_qubit_scaling_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/manifold_dependency_basin_depth_guard_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/manifold_dependency_task_matrix_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_grok_task_replication_probe_results.json` | `overclaim_risk_failed_probe` | `preserve_failed_probe_or_rerun_revised_design` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/nested_finite_geometry_holonomy_noncommutation_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/numpy_quarantine_source_native_nonclassical_gate_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/operational_manifest_source_downstream_quarantine_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/operational_manifold_assembly_true_perturbation_depth_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more boundary checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/path_entropy_schedule_confound_falsifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/result_not_all_pass_blocker_classifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/source_native_fep_online_vmp_policy_update_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/source_native_holodeck_hash_memory_placeholder_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/source_native_multicarrier_subdense_environment_contraction_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/source_native_peps3d_32_64_site_capacity_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/source_native_peps3d_52_56_60_site_regime_ladder_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/stage_record_downstream_carrier_consumption_closure_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/su2_unit_quaternion_hopf_holonomy_order_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | positive section missing, graveyard_companions section missing, boundary section missing, nearby_variants summary missing, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_adaptive_engine_switching_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_broad_numpy_import_boundary_classification_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_completion_audit_after_selector_basin_chain_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_completion_audit_and_gap_classifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_concrete_manifold_definition_and_selection_mechanism_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_final_synthesis_receipt_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_formal_stack_dynamics_closure_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_global_countermodel_completion_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_grok_97_114_boundary_ingest_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l4_entropy_cell_witness_matrix_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_adaptive_bond_trajectory_batch_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l7_xi_history_phi0_bridge_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l7_xi_history_theta_base_and_adversarial_control_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_125_134_sidequest_routing_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_137_140_sidequest_routing_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_174_175_wiki_math_sidequest_routing_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_204_212_engine_axis0_sidequest_routing_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_layer_order_noncanonical_inventory_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_peps_small_grid_dynamics_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi_engine_parameter_sweep_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi_schedule_suffix_basin_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_scale_basin_stability_map_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_schedule_memory_phase_map_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_selector_minimality_completion_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_tensor_network_lindblad_runtime_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_terrain_stage_spectral_contribution_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | one or more positive checks failed |
| `system_v5/ops/formal_scouts/results/world_model_repo_admission_gap_adapter_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, one or more boundary checks failed |
| `system_v5/ops/formal_scouts/results/xgi_hypergraph_multi_layer_coupling_centrality_probe_results.json` | `overclaim_risk_failed_probe` | `preserve_failed_probe_or_rerun_revised_design` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/xi_shell_coherent_information_gradient_adversarial_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |

## Validator Failure Notes

| kind | meaning |
| --- | --- |
| `overclaim_risk_failed_probe` | positive controls or graveyards fail, so treating this as proof would overclaim the receipt |
| `stale_noncovering_engine_core_finite_boundary_debt` | finite-boundary quarantine receipt is red because the current target gate no longer clears the old EngineCore boundary |
| `uncategorized_validator_failure` | validator failure requires manual triage before it can be used as evidence |

## Non-Formal Boundary Rows

| result | classification | blockers |
| --- | --- | --- |
| `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/carrier_readout_discriminator_matrix_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/clifford_spinor_carrier_pytorch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v0_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v1_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v2_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_associator_harden_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_axis6_order_gap_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_charge_ladder_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_finite_support_admissibility_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_gravity_knot_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_hopf_lifted_vs_density_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_qit_source_native_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_shell_capacity_2n2_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_sigma_y_holonomy_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/disc_spinor_carrier_minimality_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/discriminator_matrix_cross_row_consistency_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/external_theory_mining_catalog_v0_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_pytorch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r1_f01_finitude_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r1_f01_finitude_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r1_f01_finitude_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_pytorch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_pytorch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_envelope_medium_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_jax_medium_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_medium_pytorch_medium_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_envelope_xhigh_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_jax_xhigh_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_pytorch_xhigh_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_g2_su3_reduction_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r5_weyl_chirality_pair_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_fano_pg22_incidence_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_g2_associative_calibration_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_oph_icosahedral_screen_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_sedenion_pg32_desargues_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_foundation_r6_spin7_g2_calibration_forms_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_two_layer_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_jax_smt_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_pytorch_grad_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_three_engine_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r0_probe_quotient_refinement_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r0_probe_quotient_refinement_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r1_f01_finite_admissibility_unsat_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r1_f01_finite_admissibility_unsat_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r1_n01_noncommutation_order_quotient_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r1_n01_noncommutation_order_quotient_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r2_quotient_stability_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_high_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_high_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_high_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_low_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_low_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_low_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_medium_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_associator_xhigh_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_g2_automorphism_high_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r3_octonion_cl6_link_xhigh_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_r4_nonassoc_root_vs_carrier_discriminator_low_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_spinor_network_basins_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/godel_variants_exploration_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/knot_mass_gravity_rung_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_first_admissibility_packet_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_adm_axes_xgi_gudhi_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_adm_bracketing_xgi_toponetx_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_composition_adm_rustworkx_xgi_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_composition_axes_rustworkx_gudhi_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_quotient_adm_cvc5_xgi_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_quotient_axes_cvc5_gudhi_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_quotient_path_cvc5_rustworkx_coupling_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/modified_godel_einstein_tensor_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_anomaly_cancellation_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_charge_quantization_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_chiral_weak_from_weyl_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_clifford_minimal_ideals_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_joint_gr_sm_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_nonassoc_third_constraint_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_three_families_one_survives_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_three_gen_full_sm_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp2_weinberg_angle_explore_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp3_homochirality_cascade_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp3_matter_antimatter_chirality_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp3_yang_mills_mass_gap_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_arrow_of_time_entropy_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_chemistry_hopf_shells_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_cosmological_constant_dissolves_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_evolution_is_the_ratchet_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_fine_structure_explore_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_hierarchy_gravity_weak_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp4_measurement_retrocausal_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_cross_model_convergence_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_full_carrier_gravity_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_full_sm_gauge_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_sedenion_three_generations_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_sequential_universe_toy_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_su2u1_electroweak_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mp_universal_clock_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/nc_vs_nonassoc_setmap_scout_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/nonassoc_basin_compare_scout_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_cptp_dephasing_pinned_rho_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_cptp_dephasing_pinned_rho_pytorch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_density_entropy_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_density_entropy_pinned_rho_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_density_entropy_pinned_rho_pytorch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_density_entropy_pytorch_grad_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_engine_3qubit_face_knot_taxonomy_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/qit_source_native_three_qubit_branch_geometry_probe_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r2_quotient_stability_under_operations_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_carrier_dimension_minimum_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_carrier_property_requirements_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_div_algebra_jax_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_div_algebra_torch_leg_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_division_algebra_ladder_onset_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_entropy_as_derived_readout_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/r3_readout_invariants_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/singular_lego_wired_axis0_plural_manifold_engine_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary |
| `system_v5/ops/formal_scouts/results/spinor_network_face_readout_taxonomy_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/spinor_network_force_transition_channel_taxonomy_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/su3_color_from_g2_octonion_cl6_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_clifford_spinor_carrier_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_foundation_r0_probe_quotient_refinement_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_foundation_r1_f01_finite_admissibility_unsat_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_foundation_r1_n01_noncommutation_order_quotient_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_qit_cptp_dephasing_pinned_rho_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_qit_density_entropy_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_qit_density_entropy_pinned_rho_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_engine_tool_ladder_nested_hopf_weyl_envelope_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/three_spinor_associator_scout_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/tool_ladder_nested_hopf_weyl_jax_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/tool_ladder_nested_hopf_weyl_pytorch_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |

## Fresh-Rerun Mapping Defects

| result | validator expected source | actual source |
| --- | --- | --- |
| - | - | - |

## Backend Policy Violations

| result | source | violations |
| --- | --- | --- |
| - | - | - |

## README Missing Samples

- `system_v5/ops/formal_scouts/results/canon_algebra_artifact_v1_results.json`
- `system_v5/ops/formal_scouts/results/carrier_readout_discriminator_matrix_results.json`
- `system_v5/ops/formal_scouts/results/clifford_spinor_carrier_pytorch_leg_results.json`
- `system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v0_results.json`
- `system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v1_results.json`
- `system_v5/ops/formal_scouts/results/cross_model_readout_matrix_v2_results.json`
- `system_v5/ops/formal_scouts/results/disc_associator_harden_results.json`
- `system_v5/ops/formal_scouts/results/disc_axis6_order_gap_results.json`
- `system_v5/ops/formal_scouts/results/disc_charge_ladder_results.json`
- `system_v5/ops/formal_scouts/results/disc_finite_support_admissibility_results.json`
- `system_v5/ops/formal_scouts/results/disc_gravity_knot_results.json`
- `system_v5/ops/formal_scouts/results/disc_hopf_lifted_vs_density_results.json`
- `system_v5/ops/formal_scouts/results/disc_qit_source_native_results.json`
- `system_v5/ops/formal_scouts/results/disc_shell_capacity_2n2_results.json`
- `system_v5/ops/formal_scouts/results/disc_sigma_y_holonomy_results.json`
- `system_v5/ops/formal_scouts/results/disc_spinor_carrier_minimality_results.json`
- `system_v5/ops/formal_scouts/results/discriminator_matrix_cross_row_consistency_results.json`
- `system_v5/ops/formal_scouts/results/external_theory_mining_catalog_v0_results.json`
- `system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_jax_leg_results.json`
- `system_v5/ops/formal_scouts/results/foundation_canon_algebra_consumer_gate_pytorch_leg_results.json`
- `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v0_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_cross_model_readout_matrix_v1_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r1_f01_finitude_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r1_f01_finitude_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r1_f01_finitude_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_jax_leg_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_pytorch_leg_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_alternativity_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_g2_automorphism_xhigh_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_j3o_jordan_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_jax_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r3_sedenion_zerodivisor_pytorch_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_jax_leg_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_pytorch_leg_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_envelope_results.json`
- `system_v5/ops/formal_scouts/results/foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_jax_results.json`

## README Status Mismatches

| result | README status | index status |
| --- | --- | --- |
| `system_v5/ops/formal_scouts/results/axis0_plural_candidate_multicarrier_drive_controls_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/constraint_manifold_terrain_lindblad_composition_bridge_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/engine_core_boundary_row_triage_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/engine_core_dynamic_boundary_port_demote_classifier_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/engine_core_importer_boundary_classifier_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/result_not_all_pass_blocker_classifier_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_adaptive_engine_switching_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_axis0_layered_entropy_ratchet_audit_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_concrete_manifold_definition_and_selection_mechanism_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_engine_entropy_decay_asymptotic_and_robustness_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_formal_stack_dynamics_closure_audit_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_grok_97_114_boundary_ingest_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l4_entropy_cell_witness_matrix_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_adaptive_bond_trajectory_batch_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l7_xi_history_phi0_bridge_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_l7_xi_history_theta_base_and_adversarial_control_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_125_134_sidequest_routing_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_137_140_sidequest_routing_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_174_175_wiki_math_sidequest_routing_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_184_194_engine_tensor_sidequest_routing_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_late_grok_204_212_engine_axis0_sidequest_routing_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_layer_order_noncanonical_inventory_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_peps_small_grid_dynamics_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi_engine_parameter_sweep_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_phi_schedule_suffix_basin_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_scale_basin_stability_map_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_schedule_memory_phase_map_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_tensor_network_lindblad_runtime_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_terrain_engine_pseudo_basin_tensor_substrate_scope_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_terrain_stage_spectral_contribution_probe_results.json` | `schema_ready` | `validator_failed` |
| `system_v5/ops/formal_scouts/results/two_root_constraint_xi_causal_irreversibility_phi0_bridge_probe_results.json` | `schema_ready` | `validator_failed` |
