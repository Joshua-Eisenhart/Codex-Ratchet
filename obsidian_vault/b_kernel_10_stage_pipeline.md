---
id: "A2_3::SOURCE_MAP_PASS::b_kernel_10_stage_pipeline::a078b542b3c40de4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# b_kernel_10_stage_pipeline
**Node ID:** `A2_3::SOURCE_MAP_PASS::b_kernel_10_stage_pipeline::a078b542b3c40de4`

## Description
RQ-020 to RQ-029: B kernel accepts only declared container types, runs 10 deterministic stages (AUDIT_PROVENANCE through COMMIT), enforces undefined-term fence, derived-only fence, lexeme fence, formula guards, probe pressure, generates only ACCEPT/PARK/REJECT outcomes, writes replayable graveyard records.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[b_kernel_deterministic_stage_order]]
- **RELATED_TO** → [[b_kernel_7_stage_pipeline]]
- **RELATED_TO** → [[end_to_end_9_step_loop]]
- **RELATED_TO** → [[dual_replay_release_gate]]
- **STRUCTURALLY_RELATED** → [[b_kernel_stage_order]]

## Inward Relations
- [[01_REQUIREMENTS_LEDGER.md]] → **SOURCE_MAP_PASS**
- [[FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM]] → **RELATED_TO**
- [[a2_deterministic_tick_sequence]] → **RELATED_TO**
- [[a0_deterministic_compilation_contract]] → **RELATED_TO**
- [[a0_deterministic_truncation_contract]] → **RELATED_TO**
- [[a1_ranking_comparator]] → **RELATED_TO**
- [[b_kernel_7_stage_pipeline]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_KERNEL_PIPELINE]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_KERNEL_PIPELINE]] → **STRUCTURALLY_RELATED**
- [[B_KERNEL_7_STAGE_PIPELINE]] → **STRUCTURALLY_RELATED**
- [[DETERMINISTIC_KERNEL_PIPELINE]] → **STRUCTURALLY_RELATED**
