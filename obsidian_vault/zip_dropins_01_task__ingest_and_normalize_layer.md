---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_01_task__ingest_and_normalize_layer::fd5df308062466ce"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "NONCANON"
---

# zip_dropins_01_task__ingest_and_normalize_layer
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_01_task__ingest_and_normalize_layer::fd5df308062466ce`

## Description
01_TASK__INGEST_AND_NORMALIZE_LAYER1_OUTPUTS.task.md (1608B): TASK_ID: TSK_INGEST_AND_NORMALIZE_LAYER1_OUTPUTS TASK_KIND: MULTI_RUN_INGEST TASK_MODE: NORMALIZE  INPUT_FILES: - input/*.zip  OUTPUT_FILES: - output/LAYER1_INGEST_AND_NORMALIZATION_REPORT__A2_LAYER_1_5__multi_run_consolidation__primary_view__v1.0.md

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 4 sources, 4 batches, 7 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[input]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[01_task__ingest_and_normalize_layer1_outputs.task]]

## Inward Relations
- [[README__L1_5__WHAT_THIS_JOB_IS__v1.md]] → **SOURCE_MAP_PASS**
- [[ZIP_JOB_MANIFEST_v1.json]] → **OVERLAPS**
- [[ZIP_JOB_ROOT_AND_PAYLOAD_DISCOVERY_RULES__v1.md]] → **OVERLAPS**
- [[00_TASK__PORTABLE_OUTPUT_FILE_FENCE_AND_FAIL_CLOSED.task.md]] → **OVERLAPS**
