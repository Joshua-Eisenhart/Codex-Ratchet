# Formal Scout Readiness Index

Generated: `2026-06-09T06:12:14.590585+00:00`

Boundary: readiness index only. This does not rerun, admit, promote, or canonicalize formal scouts.

## Summary

- Result receipts indexed: `208`
- Source harnesses indexed: `477`
- Source harnesses without result receipt: `422`
- Validator pass: `15`
- Formal-scout validator fail: `4`
- Preserved validator-red rows: `0`
- Actionable validator-red rows: `4`
- Non-formal boundary rows: `189`
- README indexed receipts: `5`
- README missing receipts: `203`
- README explicit-status mismatches: `0`
- Fresh-rerun mapping defects: `0`
- Fresh-rerun dual-source defects: `0`
- Backend policy violations: `0`
- Provider receipts indexed: `4`
- Provider JSON sidecars skipped: `0`
- Provider receipt validator pass: `4`
- Provider receipt validator fail: `0`
- Provider strict-live validator pass: `2`
- Provider strict-live validator fail: `2`

## Readiness Status Counts

- `non_formal_boundary`: 189
- `schema_ready`: 15
- `validator_failed`: 4

## Validation Error Counts

- `classification is not formal_scout`: 189
- `nearby_variants summary missing`: 146
- `why_not_v4_probes missing`: 141
- `graveyard_companions section missing`: 139
- `boundary section missing`: 133
- `positive section missing`: 130
- `claim_ceiling missing`: 59
- `claim_ceiling may overclaim`: 18
- `blockers present`: 1
- `nearby_variants did not all pass`: 1
- `one or more graveyard checks failed`: 1
- `one or more positive checks failed`: 1

## Validator Failure Kind Counts

- `uncategorized_validator_failure`: 4

## Validator Failure Handling Counts

- `manual_triage_required`: 4

## Actionable vs Preserved Red Rows

- Preserved red rows: `0`
- Actionable red rows: `4`

Preserved red rows are intentionally retained as negative, nonclearance, or overclaim-boundary evidence. They are not green proofs and not current readiness-repair debt. Actionable red rows require new repair, rerun, or manual triage before closeout.

## Promotion Blocker Counts

- `formal_scout_noncanonical`: 208
- `fresh_rerun_not_performed`: 208
- `readme_index_missing`: 203
- `classification_not_formal_scout`: 189
- `non_formal_boundary`: 189
- `validator_failed`: 4

## Pass Source Counts

- `all_pass`: 198
- `missing`: 6
- `summary.all_pass`: 4

## Tool Schema Key Styles

### TOOL_MANIFEST

- `upper`: 109
- `both`: 82
- `missing`: 15
- `lower`: 2

### TOOL_INTEGRATION_DEPTH

- `upper`: 109
- `both`: 82
- `missing`: 15
- `lower`: 2

## Provider Receipt Validation

- `pass`: 4
- `fail`: 0

### Strict-Live Provider Provenance

Normal provider validation is schema/proposal-boundary validation. Strict-live validation is the provenance check for completed live-provider receipts.
- `pass`: 2
- `fail`: 2

### Strict-Live Provider Error Counts

- `strict-live completed provider receipt missing raw_response or live_api_proof`: 2

## Validator Failed Rows

| result | failure kind | handling | resolution surface | errors |
| --- | --- | --- | --- | --- |
| `system_v5/ops/formal_scouts/results/holodeck_basin_grade_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/holodeck_core_prediction_memory_seed_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/holodeck_qit_spinor_memory_adapter_seed_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/xi_shell_coherent_information_gradient_adversarial_audit_probe_results.json` | `uncategorized_validator_failure` | `manual_triage_required` | `-` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |

## Validator Failure Notes

| kind | meaning |
| --- | --- |
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
| `system_v5/ops/formal_scouts/results/godel_variants_exploration_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/knot_mass_gravity_rung_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
| `system_v5/ops/formal_scouts/results/mc_first_admissibility_packet_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |
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
| `system_v5/ops/formal_scouts/results/three_spinor_associator_scout_results.json` | `scratch_diagnostic` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary, readme_index_missing |

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
| - | - | - |
