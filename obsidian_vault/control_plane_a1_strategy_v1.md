---
id: "A2_3::SOURCE_MAP_PASS::control_plane_a1_strategy_v1::4c0c7c500ebbaf37"
type: "REFINED_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "SOURCE_CLAIM"
---

# control_plane_a1_strategy_v1
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_a1_strategy_v1::4c0c7c500ebbaf37`

## Description
A1_STRATEGY_v1.md (5496B):  # A1_STRATEGY v1  This specification defines the only admissible A1 strategy object to be transported in: - `A1_TO_A0_STRATEGY_ZIP` as `A1_STRATEGY_v1.json`.  This is a **non-kernel** artifact. B never sees it.  NOTE: Outcome `PARK` is reserved exclusively for ZIP_PROTOCOL_v2 sequence-gap handling.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 5 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[zip_protocol_v2]]
- **DEPENDS_ON** → [[a1_strategy_v1]]
- **DEPENDS_ON** → [[object]]
- **DEPENDS_ON** → [[ZIP_PROTOCOL_V2]]

## Inward Relations
- [[00_TASK__INGEST_AND_VALIDATE_WORKER_OUTPUTS.task.md]] → **SOURCE_MAP_PASS**
- [[MANIFEST.json]] → **OVERLAPS**
