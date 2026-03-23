---
id: "A2_3::ENGINE_PATTERN_PASS::B_Message_Discipline::16d637d69581f70d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# B_Message_Discipline
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::B_Message_Discipline::16d637d69581f70d`

## Description
Messages must be exactly COMMAND_MESSAGE (REQUEST lines only) or ARTIFACT_MESSAGE (one EXPORT_BLOCK, one SNAPSHOT, or SIM_EVIDENCE_PACK). Anything else → REJECT_MESSAGE TAG MULTI_ARTIFACT_OR_PROSE. No comments in artifacts.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[message_discipline]]

## Inward Relations
- [[BOOTPACK_THREAD_B_v3.9.13.md]] → **ENGINE_PATTERN_PASS**
