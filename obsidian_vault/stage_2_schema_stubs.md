---
id: "A2_3::SOURCE_MAP_PASS::stage_2_schema_stubs::57ed349c0a3c02f2"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# stage_2_schema_stubs
**Node ID:** `A2_3::SOURCE_MAP_PASS::stage_2_schema_stubs::57ed349c0a3c02f2`

## Description
4 Stage-2 schema stubs: ZIP_JOB_MANIFEST, A2_BRAIN_UPDATE_PACKET, A1_BRAIN_ROSETTA_UPDATE_PACKET, RATCHET_FUEL_CANDIDATE_PACKET. Bootpacks reference schemas, job artifacts validate against them, validation failure is fail-closed. Active validators: zip_job_bundle_validator.py, stage2_schema_gate.py.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 2 sources, 2 batches, 9 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **RELATED_TO** → [[stage_2_validation_behavior]]
- **DEPENDS_ON** → [[reference]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md]] → **SOURCE_MAP_PASS**
- [[28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md]] → **OVERLAPS**
- [[B_KERNEL_LINE_FENCE_VALIDATION]] → **RELATED_TO**
- [[COMMENT_BAN_ENFORCEMENT]] → **RELATED_TO**
- [[zip_dropins_readme]] → **DEPENDS_ON**
- [[28_stage_2_job_schemas_and_validation_stubs__v1]] → **STRUCTURALLY_RELATED**
