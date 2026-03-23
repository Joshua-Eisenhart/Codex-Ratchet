---
id: "A2_3::ENGINE_PATTERN_PASS::COMMENT_BAN_ENFORCEMENT::4234da1fe09b69d6"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# COMMENT_BAN_ENFORCEMENT
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::COMMENT_BAN_ENFORCEMENT::4234da1fe09b69d6`

## Description
Lines starting with '#' or '//' are banned in all SIM_EVIDENCE and SNAPSHOT messages. This prevents prose/annotation from contaminating structured artifacts. The gateway checks this before any content parsing.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[stage_2_schema_stubs]]
- **RELATED_TO** → [[stage_2_validation_behavior]]

## Inward Relations
- [[sim_dispatcher.py]] → **ENGINE_PATTERN_PASS**
- [[B_KERNEL_LINE_FENCE_VALIDATION]] → **RELATED_TO**
