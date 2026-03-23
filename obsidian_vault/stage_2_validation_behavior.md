---
id: "A2_3::SOURCE_MAP_PASS::stage_2_validation_behavior::60f992ef79c2e1c1"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# stage_2_validation_behavior
**Node ID:** `A2_3::SOURCE_MAP_PASS::stage_2_validation_behavior::60f992ef79c2e1c1`

## Description
Job artifacts should validate against schemas before acceptance. Failing validation equals fail-closed (using zip_job_bundle_validator.py and stage2_schema_gate.py).

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[stage_3_validation_flow]]

## Inward Relations
- [[28_STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1.md]] → **SOURCE_MAP_PASS**
- [[stage_2_schema_stubs]] → **RELATED_TO**
- [[B_KERNEL_LINE_FENCE_VALIDATION]] → **RELATED_TO**
- [[COMMENT_BAN_ENFORCEMENT]] → **RELATED_TO**
- [[28_stage_2_job_schemas_and_validation_stubs__v1]] → **STRUCTURALLY_RELATED**
