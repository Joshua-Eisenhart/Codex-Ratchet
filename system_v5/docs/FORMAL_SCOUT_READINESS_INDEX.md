# Formal Scout Readiness Index

Generated: `2026-05-22T03:13:40.402845+00:00`

Boundary: readiness index only. This does not rerun, admit, promote, or canonicalize formal scouts.

## Summary

- Result receipts indexed: `362`
- Source harnesses indexed: `362`
- Source harnesses without result receipt: `0`
- Validator pass: `347`
- Formal-scout validator fail: `14`
- Preserved validator-red rows: `14`
- Actionable validator-red rows: `0`
- Non-formal boundary rows: `1`
- README indexed receipts: `362`
- README missing receipts: `0`
- README explicit-status mismatches: `0`
- Fresh-rerun mapping defects: `0`
- Fresh-rerun dual-source defects: `0`
- Backend policy violations: `0`
- Provider receipts indexed: `778`
- Provider receipt validator pass: `778`
- Provider receipt validator fail: `0`
- Provider strict-live validator pass: `625`
- Provider strict-live validator fail: `153`

## Readiness Status Counts

- `schema_ready`: 347
- `validator_failed`: 14
- `non_formal_boundary`: 1

## Validation Error Counts

- `one or more positive checks failed`: 15
- `blockers present`: 14
- `nearby_variants did not all pass`: 12
- `one or more graveyard checks failed`: 12
- `one or more boundary checks failed`: 2
- `classification is not formal_scout`: 1
- `nearby_variants summary missing`: 1
- `why_not_v4_probes missing`: 1

## Validator Failure Kind Counts

- `stale_noncovering_engine_core_finite_boundary_debt`: 10
- `overclaim_risk_failed_probe`: 3
- `true_failed_readout_probe`: 1

## Validator Failure Handling Counts

- `preserve_red_nonclearance`: 10
- `preserve_failed_probe_or_rerun_revised_design`: 3
- `preserve_negative_result_until_revised_design`: 1

## Actionable vs Preserved Red Rows

- Preserved red rows: `14`
- Actionable red rows: `0`

Preserved red rows are intentionally retained as negative, nonclearance, or overclaim-boundary evidence. They are not green proofs and not current readiness-repair debt. Actionable red rows require new repair, rerun, or manual triage before closeout.

## Promotion Blocker Counts

- `formal_scout_noncanonical`: 362
- `fresh_rerun_not_performed`: 362
- `validator_failed`: 14
- `classification_not_formal_scout`: 1
- `non_formal_boundary`: 1

## Pass Source Counts

- `all_pass`: 249
- `summary.all_pass`: 78
- `derived_formal_scout_sections`: 35

## Tool Schema Key Styles

### TOOL_MANIFEST

- `upper`: 222
- `both`: 77
- `lower`: 63

### TOOL_INTEGRATION_DEPTH

- `upper`: 223
- `both`: 76
- `lower`: 63

## Provider Receipt Validation

- `pass`: 778
- `fail`: 0

### Strict-Live Provider Provenance

Normal provider validation is schema/proposal-boundary validation. Strict-live validation is the provenance check for completed live-provider receipts.
- `pass`: 625
- `fail`: 153

### Strict-Live Provider Error Counts

- `strict-live completed provider receipt missing raw_response or live_api_proof`: 151
- `strict-live normalized receipt source_raw_receipt path missing`: 6

## Validator Failed Rows

| result | failure kind | handling | resolution surface | errors |
| --- | --- | --- | --- | --- |
| `system_v5/ops/formal_scouts/results/chiral_trajectory_persistent_homology_readout_feature_probe_results.json` | `true_failed_readout_probe` | `preserve_negative_result_until_revised_design` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | one or more positive checks failed, one or more boundary checks failed |
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
| `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_global_structure_probe_results.json` | `overclaim_risk_failed_probe` | `preserve_failed_probe_or_rerun_revised_design` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | one or more positive checks failed, one or more boundary checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/multiqubit_qit_reservoir_grok_task_replication_probe_results.json` | `overclaim_risk_failed_probe` | `preserve_failed_probe_or_rerun_revised_design` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |
| `system_v5/ops/formal_scouts/results/xgi_hypergraph_multi_layer_coupling_centrality_probe_results.json` | `overclaim_risk_failed_probe` | `preserve_failed_probe_or_rerun_revised_design` | `system_v5/ops/formal_scouts/results/formal_scout_readiness_debt_classification_probe_results.json` | nearby_variants did not all pass, one or more positive checks failed, one or more graveyard checks failed, blockers present |

## Validator Failure Notes

| kind | meaning |
| --- | --- |
| `overclaim_risk_failed_probe` | positive controls or graveyards fail, so treating this as proof would overclaim the receipt |
| `stale_noncovering_engine_core_finite_boundary_debt` | finite-boundary quarantine receipt is red because the current target gate no longer clears the old EngineCore boundary |
| `true_failed_readout_probe` | persistence readout clears its own accuracy floor but loses to the raw-trajectory baseline and remains an open negative result |

## Non-Formal Boundary Rows

| result | classification | blockers |
| --- | --- | --- |
| `system_v5/ops/formal_scouts/results/singular_lego_wired_axis0_plural_manifold_engine_probe_results.json` | `tool_lego_fit_probe` | classification_not_formal_scout, formal_scout_noncanonical, fresh_rerun_not_performed, non_formal_boundary |

## Fresh-Rerun Mapping Defects

| result | validator expected source | actual source |
| --- | --- | --- |
| - | - | - |

## Backend Policy Violations

| result | source | violations |
| --- | --- | --- |
| - | - | - |

## README Missing Samples

- none

## README Status Mismatches

| result | README status | index status |
| --- | --- | --- |
| - | - | - |
