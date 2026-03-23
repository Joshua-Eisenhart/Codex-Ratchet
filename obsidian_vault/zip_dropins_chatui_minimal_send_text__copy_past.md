---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_chatui_minimal_send_text__copy_past::4287e4cf8b972496"
type: "KERNEL_CONCEPT"
layer: "A1_JARGONED"
authority: "CROSS_VALIDATED"
---

# zip_dropins_chatui_minimal_send_text__copy_past
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_chatui_minimal_send_text__copy_past::4287e4cf8b972496`

## Description
CHATUI_MINIMAL_SEND_TEXT__COPY_PASTE.md (937B): Run this ZIP_JOB exactly. Execute all tasks in order from `meta/ZIP_JOB_MANIFEST_v1.json`.  Hard rules: - First, apply: `meta/ZIP_JOB_ROOT_AND_PAYLOAD_DISCOVERY_RULES__SINGLE_ATTACHMENT_AND_SEPARATE_PAYLOAD_ATTACHMENT_COMPAT__v1.md`. - Treat the PAYL

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 12 sources, 12 batches, 16 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[send_text]]
- **DEPENDS_ON** → [[chatui_minimal_send_text__copy_paste]]
- **DEPENDS_ON** → [[zip_job_root_and_payload_discovery_rules__single_a]]
- **ROSETTA_MAP** → [[ZIP_DROPINS_CHATUI_MINIMAL_SEND_TEXT_COPY_PAST]]

## Inward Relations
- [[QUALITY_GATE_REPORT.out.md]] → **SOURCE_MAP_PASS**
- [[SELF_AUDIT_AND_REPAIR_LOG.out.md]] → **OVERLAPS**
- [[CHATUI_MINIMAL_SEND_TEXT__COPY_PASTE.md]] → **OVERLAPS**
- [[BRAIN_BOOT_ACK__A2_A1_PERSISTENT_BRAIN_AND_PROCESS_LOAD_CONFIRMATION.out.md]] → **OVERLAPS**
- [[README__L1_5__WHAT_THIS_JOB_IS__v1.md]] → **OVERLAPS**
- [[ZIP_JOB_MANIFEST_v1.json]] → **OVERLAPS**
- [[ZIP_JOB_ROOT_AND_PAYLOAD_DISCOVERY_RULES__v1.md]] → **OVERLAPS**
- [[00_TASK__PORTABLE_OUTPUT_FILE_FENCE_AND_FAIL_CLOSED.task.md]] → **OVERLAPS**
- [[FILE_FENCE_PROTOCOL.md]] → **OVERLAPS**
- [[QUALITY_GATE_REPORT.out.md]] → **OVERLAPS**
- [[02_TASK__MATH_ASSUMPTION_AND_RETOOL_MAP.task.md]] → **OVERLAPS**
- [[03_TASK__RATCHET_FUEL_SELECTION_MATRIX.task.md]] → **OVERLAPS**
- [[chatui_minimal_send_text__copy_paste]] → **STRUCTURALLY_RELATED**
- [[ZIP_DROPINS_CHATUI_MINIMAL_SEND_TEXT_COPY_PAST]] → **STRIPPED_FROM**
