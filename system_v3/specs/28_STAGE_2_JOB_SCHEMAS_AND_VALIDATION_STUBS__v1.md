# STAGE_2_JOB_SCHEMAS_AND_VALIDATION_STUBS__v1
Status: DRAFT / NONCANON
Date: 2026-03-03
Owner: Stage-2 schema hardening

## Purpose
Provide strict schema stubs for Stage-2 bootpack outputs.
Executable validator helpers already exist for active ZIP/job paths, but enforcement is still path-specific rather than universal.

## Files
1. `system_v3/specs/schemas/ZIP_JOB_MANIFEST_STAGE2_v1.schema.json`
2. `system_v3/specs/schemas/A2_BRAIN_UPDATE_PACKET_STAGE2_v1.schema.json`
3. `system_v3/specs/schemas/A1_BRAIN_ROSETTA_UPDATE_PACKET_STAGE2_v1.schema.json`
4. `system_v3/specs/schemas/RATCHET_FUEL_CANDIDATE_PACKET_STAGE2_v1.schema.json`

## Stage-2 Required Behavior
1. Bootpacks must reference these schema files.
2. Job artifacts should validate against these schemas before being accepted as Stage-2 outputs.
3. Validation failure must be fail-closed and reported.
4. Current active validator helpers include:
   - `system_v3/tools/zip_job_bundle_validator.py`
   - `system_v3/tools/stage2_schema_gate.py`

## Compatibility
- Existing templates may still carry migration aliases while validator rollout is being tightened.
- Schema stubs intentionally avoid forcing legacy field aliases.

## Next Step
Stage-3 should expand mandatory use of the existing executable validators, tighten schema coverage, and normalize deterministic pass/fail reporting across producers.
