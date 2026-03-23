---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_05_task__quality_gate_and_path_conf::9d5bc9c34523de17"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "NONCANON"
---

# zip_dropins_05_task__quality_gate_and_path_conf
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_05_task__quality_gate_and_path_conf::9d5bc9c34523de17`

## Description
05_TASK__QUALITY_GATE_AND_PATH_CONFORMANCE.task.md (1300B): TASK_ID: TSK_QUALITY_GATE_AND_PATH_CONFORMANCE TASK_KIND: QUALITY_GATE TASK_MODE: FAIL_CLOSED  INPUT_FILES: - meta/ZIP_JOB_MANIFEST_v1.json - output/*  OUTPUT_FILES: - output/QUALITY_GATE_REPORT__A2_LAYER_1_5__multi_run_consolidation__primary_view__v

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 4 sources, 4 batches, 7 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[input]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[05_task__quality_gate_and_path_conformance.task]]

## Inward Relations
- [[README__L1_5__WHAT_THIS_JOB_IS__v1.md]] → **SOURCE_MAP_PASS**
- [[ZIP_JOB_MANIFEST_v1.json]] → **OVERLAPS**
- [[ZIP_JOB_ROOT_AND_PAYLOAD_DISCOVERY_RULES__v1.md]] → **OVERLAPS**
- [[00_TASK__PORTABLE_OUTPUT_FILE_FENCE_AND_FAIL_CLOSED.task.md]] → **OVERLAPS**
