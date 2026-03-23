---
id: "A2_3::SOURCE_MAP_PASS::control_plane_zip_job_manifest_v1::7042eb4f20aa88c1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_zip_job_manifest_v1
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_zip_job_manifest_v1::7042eb4f20aa88c1`

## Description
ZIP_JOB_MANIFEST_v1.json (891B): {   "schema": "ZIP_JOB_MANIFEST_v1",   "zip_job_kind": "A1_CONSOLIDATION_PREPACK_JOB",   "producer_role": "A1_CONSOLIDATOR",   "consumer_role": "A1_CONSOLIDATOR",   "producer": "A1",   "consumer": "A1",   "task_execution_order": [     "tasks/00_TASK__INGEST_AND_VALIDATE_WORKER_OUTPUTS.task.md",     

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[a1_consolidation_prepack_job]]
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[worker]]

## Inward Relations
- [[00_README.md]] → **SOURCE_MAP_PASS**
