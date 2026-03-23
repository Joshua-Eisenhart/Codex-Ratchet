---
id: "A2_3::SOURCE_MAP_PASS::a0_deterministic_truncation_contract::160780a9c1c0df14"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# a0_deterministic_truncation_contract
**Node ID:** `A2_3::SOURCE_MAP_PASS::a0_deterministic_truncation_contract::160780a9c1c0df14`

## Description
When budget overflow occurs: drop lowest-priority bucket first, then reverse lexical order, then highest dependency depth, then latest branch ID. Dropped items appended to carryover queue with reason BUDGET_TRUNCATED.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[a2_deterministic_tick_sequence]]
- **RELATED_TO** → [[b_kernel_10_stage_pipeline]]
- **RELATED_TO** → [[b_kernel_deterministic_stage_order]]
- **RELATED_TO** → [[a1_ranking_comparator]]
- **RELATED_TO** → [[dual_replay_release_gate]]

## Inward Relations
- [[04_A0_COMPILER_SPEC.md]] → **SOURCE_MAP_PASS**
- [[a0_budget_and_truncation]] → **RELATED_TO**
- [[a0_deterministic_compilation_contract]] → **RELATED_TO**
