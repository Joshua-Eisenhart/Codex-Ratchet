# BOOTPACK_A2_REFINERY__v1
Status: DRAFT / NONCANON
Date: 2026-03-03
Owner: A2 refinery execution lane

## Purpose
Provide a strict, reusable execution contract for A2 high-entropy extraction jobs.
This bootpack prioritizes over-capture, invariant locks, contradiction preservation, and fail-closed output completeness.

## Inputs
Required context inputs:
1. `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
2. `system_v3/a2_state/INTENT_SUMMARY.md`
3. `system_v3/a2_state/MODEL_CONTEXT.md` (overlay; non-authoritative)
4. Stage-0 naming rules:
   `system_v3/specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md`

Required payload input:
- One or more high-entropy source docs.

## Non-Negotiable Rules
1. No narrative smoothing.
2. Contradictions are first-class outputs.
3. Unknown or missing locator provenance must be labeled `UNVERIFIED`.
4. Do not infer canon truth.
5. If required outputs are missing, fail closed.

## Execution Order (strict)
1. Normalize input text and emit shard report.
2. Build topic index and topic directory plan.
3. Run topic-level extraction packets.
4. Run invariant-lock pass.
5. Emit document-level manifest and summary.
6. Emit A2/A1 brain delta packets.
7. Run quality gate and fail-closed completeness check.

## Invariant-Lock Requirements
If present in source, extraction must explicitly capture:
1. Type-1/Type-2 engine mappings.
2. Outer/Inner structure.
3. `WIN/LOSE` vs `win/lose` semantics.
4. Deductive/Inductive split.
5. T-then-F ordering.
6. Eight-strategy completeness.

Missing any detected lock in output => quality gate failure.

## Required Outputs
1. `DOCUMENT_NORMALIZATION_AND_SHARD_REPORT`
2. `DOCUMENT_TOPIC_INDEX`
3. `DOCUMENT_META_MANIFEST`
4. `DOCUMENT_GENERAL_SUMMARY`
5. Per-topic packet set:
   - `TOPIC_CARD`
   - `TOPIC_INTENT_MAP`
   - `TOPIC_CONTEXT_MAP`
   - `TOPIC_CONTRADICTION_MAP`
   - `TOPIC_SUMMARY`
   - `TOPIC_INTERPRETATION_MAP`
   - `TOPIC_TERM_INDEX`
6. `A2_BRAIN_UPDATE_PACKET`
7. `A1_BRAIN_ROSETTA_UPDATE_PACKET`
8. `QUALITY_GATE_REPORT`

## Output Validation Stub
Stage-2 schema stubs:
- `system_v3/specs/schemas/ZIP_JOB_MANIFEST_STAGE2_v1.schema.json`
- `system_v3/specs/schemas/A2_BRAIN_UPDATE_PACKET_STAGE2_v1.schema.json`
- `system_v3/specs/schemas/A1_BRAIN_ROSETTA_UPDATE_PACKET_STAGE2_v1.schema.json`

## Naming
All new artifacts from this bootpack must follow Stage-0 naming freeze.

