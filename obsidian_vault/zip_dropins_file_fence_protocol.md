---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_file_fence_protocol::126845cde41c7898"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# zip_dropins_file_fence_protocol
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_file_fence_protocol::126845cde41c7898`

## Description
FILE_FENCE_PROTOCOL.md (175B): # File fence protocol (must follow exactly)  You must output files using these fences and nothing else:  BEGIN FILE: <relative/path> <file content> END FILE: <relative/path>  

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 3 sources, 3 batches, 9 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[file_fence_protocol]]

## Inward Relations
- [[FILE_FENCE_PROTOCOL.md]] → **SOURCE_MAP_PASS**
- [[03_TASK__RATCHET_FUEL_SELECTION_MATRIX.task.md]] → **OVERLAPS**
- [[ZIP_JOB_MANIFEST_v1.json]] → **OVERLAPS**
- [[zip_dropins_00_task__portable_output_file_fence]] → **STRUCTURALLY_RELATED**
- [[00_task__portable_output_file_fence_and_fail_close]] → **STRUCTURALLY_RELATED**
- [[00_task__portable_output_file_fence_contract_and_f]] → **STRUCTURALLY_RELATED**
- [[file_fence_protocol]] → **STRUCTURALLY_RELATED**
