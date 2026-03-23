---
id: "A2_3::SOURCE_MAP_PASS::b_kernel_deterministic_stage_order::a1e953226e3ebe1e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# b_kernel_deterministic_stage_order
**Node ID:** `A2_3::SOURCE_MAP_PASS::b_kernel_deterministic_stage_order::a1e953226e3ebe1e`

## Description
B kernel runs exactly 10 fixed stages: (1) AUDIT_PROVENANCE, (1.5) DERIVED_ONLY_GUARD, (1.55) CONTENT_DIGIT_GUARD, (1.6) UNDEFINED_TERM_FENCE, (2) SCHEMA_CHECK, (3) DEPENDENCY_GRAPH, (4) NEAR_DUPLICATE, (5) PRESSURE, (6) EVIDENCE_UPDATE, (7) COMMIT. No reordering permitted.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[end_to_end_9_step_loop]]
- **RELATED_TO** → [[dual_replay_release_gate]]
- **STRUCTURALLY_RELATED** → [[b_kernel_stage_order]]

## Inward Relations
- [[03_B_KERNEL_SPEC.md]] → **SOURCE_MAP_PASS**
- [[b_kernel_10_stage_pipeline]] → **RELATED_TO**
- [[b_kernel_7_stage_pipeline]] → **RELATED_TO**
- [[FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM]] → **RELATED_TO**
- [[a2_deterministic_tick_sequence]] → **RELATED_TO**
- [[a0_deterministic_compilation_contract]] → **RELATED_TO**
- [[a0_deterministic_truncation_contract]] → **RELATED_TO**
- [[a1_ranking_comparator]] → **RELATED_TO**
- [[B_Deterministic_10_Stage_Order]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_KERNEL_PIPELINE]] → **STRUCTURALLY_RELATED**
- [[b_kernel_7_stage_pipeline]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_KERNEL_PIPELINE]] → **STRUCTURALLY_RELATED**
- [[B_KERNEL_7_STAGE_PIPELINE]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_KERNEL_PIPELINE]] → **STRUCTURALLY_RELATED**
