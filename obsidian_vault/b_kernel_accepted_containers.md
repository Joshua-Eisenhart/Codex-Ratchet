---
id: "A2_3::SOURCE_MAP_PASS::b_kernel_accepted_containers::b2e39baf54977d5d"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# b_kernel_accepted_containers
**Node ID:** `A2_3::SOURCE_MAP_PASS::b_kernel_accepted_containers::b2e39baf54977d5d`

## Description
B Kernel accepts only EXPORT_BLOCK vN, SIM_EVIDENCE v1, and THREAD_S_SAVE_SNAPSHOT v2. Everything else is REJECTED.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 1 sources, 2 batches, 6 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[sim_evidence]]
- **DEPENDS_ON** → [[sim_evidence_v1]]
- **DEPENDS_ON** → [[thread_s_save_snapshot_v2]]
- **DEPENDS_ON** → [[export_block]]

## Inward Relations
- [[03_B_KERNEL_SPEC.md]] → **SOURCE_MAP_PASS**
- [[B_Accepted_Containers]] → **RELATED_TO**
