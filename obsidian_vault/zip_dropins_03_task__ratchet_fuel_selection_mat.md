---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__ratchet_fuel_selection_mat::e7df433187482258"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# zip_dropins_03_task__ratchet_fuel_selection_mat
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_03_task__ratchet_fuel_selection_mat::e7df433187482258`

## Description
03_TASK__RATCHET_FUEL_SELECTION_MATRIX.task.md (561B): TASK_ID: TSK_RATCHET_FUEL_SELECTION TASK_KIND: RATCHET_FUEL_SELECTION_MATRIX TASK_MODE: CLASSIFY  INPUT_FILES: - input/RESEARCH_TOPIC_BRIEF.md - input/RESEARCH_SEED_NOTES.md  OUTPUT_FILES: - output/RATCHET_FUEL_SELECTION_MATRIX__EXTERNAL_RESEARCH_RET

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 3 sources, 3 batches, 11 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[input]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[external]]
- **DEPENDS_ON** → [[03_task__ratchet_fuel_selection_matrix.task]]
- **DEPENDS_ON** → [[research_topic_brief]]
- **DEPENDS_ON** → [[research_seed_notes]]
- **DEPENDS_ON** → [[seed_notes]]
- **DEPENDS_ON** → [[topic_brief]]

## Inward Relations
- [[FILE_FENCE_PROTOCOL.md]] → **SOURCE_MAP_PASS**
- [[02_TASK__MATH_ASSUMPTION_AND_RETOOL_MAP.task.md]] → **OVERLAPS**
- [[03_TASK__RATCHET_FUEL_SELECTION_MATRIX.task.md]] → **OVERLAPS**
