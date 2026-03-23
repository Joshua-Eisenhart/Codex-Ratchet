---
id: "A2_3::SOURCE_MAP_PASS::control_plane_a0_save_summary_v1::8562e261beb49629"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_a0_save_summary_v1
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_a0_save_summary_v1::8562e261beb49629`

## Description
A0_SAVE_SUMMARY_v1.md (996B): # A0_SAVE_SUMMARY v1  Defines the canonical informational summary object carried in: - `A0_TO_A1_SAVE_ZIP` as `A0_SAVE_SUMMARY.json`  This object is informational only and is not a mutation container.  ## Required fields  - `schema`: MUST equal `"A0_SAVE_SUMMARY_v1"` - `run_id`: string - `last_seque

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[a0_save_summary]]
- **DEPENDS_ON** → [[a0_save_summary_v1]]
- **DEPENDS_ON** → [[string]]
- **DEPENDS_ON** → [[object]]

## Inward Relations
- [[00_TASK__INGEST_AND_VALIDATE_WORKER_OUTPUTS.task.md]] → **SOURCE_MAP_PASS**
