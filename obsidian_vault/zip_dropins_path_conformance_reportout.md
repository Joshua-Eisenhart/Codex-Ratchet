---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_path_conformance_reportout::92987eb4a5d8b869"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# zip_dropins_path_conformance_reportout
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_path_conformance_reportout::92987eb4a5d8b869`

## Description
PATH_CONFORMANCE_REPORT.out.md (213B): # PATH_CONFORMANCE_REPORT  status: PASS|FAIL  checks: - required_output_paths_exact_match_manifest: YES|NO - extra_unmanifested_outputs_absent: YES|NO - missing_manifest_outputs_absent: YES|NO  failed_paths: - [] 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 6 sources, 6 batches, 9 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[path_conformance_report.out]]

## Inward Relations
- [[00A_TASK__BRAIN_BOOT_ACK__PERSISTENT_BRAIN_AND_PAYLOAD_DISCOVERY.task.md]] → **SOURCE_MAP_PASS**
- [[BRAIN_BOOT_ACK__A2_A1_PERSISTENT_BRAIN_AND_PROCESS_LOAD_CONFIRMATION.out.md]] → **OVERLAPS**
- [[README__L1_5__WHAT_THIS_JOB_IS__v1.md]] → **OVERLAPS**
- [[ZIP_JOB_MANIFEST_v1.json]] → **OVERLAPS**
- [[ZIP_JOB_ROOT_AND_PAYLOAD_DISCOVERY_RULES__v1.md]] → **OVERLAPS**
- [[00_TASK__PORTABLE_OUTPUT_FILE_FENCE_AND_FAIL_CLOSED.task.md]] → **OVERLAPS**
- [[path_conformance_report.out]] → **STRUCTURALLY_RELATED**
