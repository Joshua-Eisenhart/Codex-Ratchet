---
id: "A2_3::SOURCE_MAP_PASS::gemini_deep_read_sop_execution_protocol::88c60f839d7b0e91"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# gemini_deep_read_sop_execution_protocol
**Node ID:** `A2_3::SOURCE_MAP_PASS::gemini_deep_read_sop_execution_protocol::88c60f839d7b0e91`

## Description
Operational context: This is the exact code and instruction set required for Gemini to push extracted concepts to the graph. Do not write custom scripts, use the exact python snippet provided in this SOP: # Gemini Deep-Read Cross-Validation SOP
**TARGET:** Any LLM Agent executing the manual Deep-Read pass.

## Mission Context
Claude previously ingested ~3,600 files using a "shallow" batch script that only read the first 800 characters and auto-generated poor concepts.
Your job is to read the FULL files, extract deep formal constraints/Architectures, and inject them into the graph to validate and en

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[constraints]]
- **DEPENDS_ON** → [[agent]]

## Inward Relations
- [[GEMINI_DEEP_READ_SOP.md]] → **SOURCE_MAP_PASS**
