# Formal Scout Readiness Index

Generated: `2026-05-18T06:43:41.845618+00:00`

Boundary: readiness index only. This does not rerun, admit, promote, or canonicalize formal scouts.

## Summary

- Result receipts indexed: `192`
- Source harnesses indexed: `189`
- Source harnesses without result receipt: `0`
- Validator pass: `186`
- Validator fail: `6`
- README indexed receipts: `187`
- README missing receipts: `5`
- Fresh-rerun mapping defects: `0`
- Fresh-rerun dual-source defects: `0`
- Backend policy violations: `0`
- Provider receipts indexed: `238`
- Provider receipt validator pass: `238`
- Provider receipt validator fail: `0`

## Readiness Status Counts

- `schema_ready`: 186
- `source_missing`: 3
- `validator_failed`: 3

## Validation Error Counts

- `nearby_variants summary missing`: 6
- `why_not_v4_probes missing`: 6
- `classification is not formal_scout`: 4
- `boundary section missing`: 3
- `claim_ceiling missing`: 3
- `graveyard_companions section missing`: 3
- `positive section missing`: 3
- `promotion_allowed is not false`: 3
- `blockers present`: 1
- `one or more graveyard checks failed`: 1
- `one or more positive checks failed`: 1

## Promotion Blocker Counts

- `formal_scout_noncanonical`: 192
- `fresh_rerun_not_performed`: 192
- `readme_index_missing`: 5
- `classification_not_formal_scout`: 4
- `promotion_allowed_not_false`: 3
- `source_missing`: 3
- `validator_failed`: 3

## Tool Schema Key Styles

### TOOL_MANIFEST

- `upper`: 144
- `lower`: 32
- `both`: 13
- `missing`: 3

### TOOL_INTEGRATION_DEPTH

- `upper`: 144
- `lower`: 32
- `both`: 13
- `missing`: 3

## Provider Receipt Validation

- `pass`: 238
- `fail`: 0

## Validator Failed Rows

| result | status | errors |
| --- | --- | --- |
| `system_v5/ops/formal_scouts/results/commutative_geometry_collapse_falsifier_cvc5_dual_solver_crosscheck_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/constraint_manifold_placement_neural_behavior_discrimination_probe_results.json` | `validator_failed` | why_not_v4_probes missing, nearby_variants summary missing, one or more graveyard checks failed |
| `system_v5/ops/formal_scouts/results/d4_pseudoscalar_chirality_portability_extension_results.json` | `source_missing` | classification is not formal_scout, promotion_allowed is not false, claim_ceiling missing, positive section missing, graveyard_companions section missing, boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/d5_portability_n6_n7_extension_results.json` | `source_missing` | classification is not formal_scout, promotion_allowed is not false, claim_ceiling missing, positive section missing, graveyard_companions section missing, boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/d5_portability_signature_sweep_results.json` | `source_missing` | classification is not formal_scout, promotion_allowed is not false, claim_ceiling missing, positive section missing, graveyard_companions section missing, boundary section missing, why_not_v4_probes missing, nearby_variants summary missing |
| `system_v5/ops/formal_scouts/results/singular_lego_wired_axis0_plural_manifold_engine_probe_results.json` | `validator_failed` | classification is not formal_scout, why_not_v4_probes missing, nearby_variants summary missing, one or more positive checks failed, blockers present |

## Fresh-Rerun Mapping Defects

| result | validator expected source | actual source |
| --- | --- | --- |
| - | - | - |

## Backend Policy Violations

| result | source | violations |
| --- | --- | --- |
| - | - | - |

## README Missing Samples

- `system_v5/ops/formal_scouts/results/d4_pseudoscalar_chirality_dimension_parity_portability_probe_results.json`
- `system_v5/ops/formal_scouts/results/d4_pseudoscalar_chirality_portability_extension_results.json`
- `system_v5/ops/formal_scouts/results/d5_commutative_geometry_collapse_15_signature_portability_probe_results.json`
- `system_v5/ops/formal_scouts/results/d5_portability_n6_n7_extension_results.json`
- `system_v5/ops/formal_scouts/results/d5_portability_signature_sweep_results.json`
