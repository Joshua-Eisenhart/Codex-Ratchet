---
id: "A2_3::SOURCE_MAP_PASS::browser_determinism_boundary::01d6a2d9d262652e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# browser_determinism_boundary
**Node ID:** `A2_3::SOURCE_MAP_PASS::browser_determinism_boundary::01d6a2d9d262652e`

## Description
Browser reasoning is inherently nondeterministic. The automation step itself must be deterministic: one job = one ZIP bundle + one doc + one send-text payload.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[zip_job_deterministic_carrier]]
- **DEPENDS_ON** → [[send_text]]

## Inward Relations
- [[30_CHATUI_CLAW_PLAYWRIGHT_PROTOCOL_v1.md]] → **SOURCE_MAP_PASS**
- [[a0_deterministic_canonicalization]] → **RELATED_TO**
- [[A0_Deterministic_Bridge]] → **RELATED_TO**
