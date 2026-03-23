---
id: "A2_3::ENGINE_PATTERN_PASS::LLM_OUTPUT_QUARANTINE_PATTERN::5689ca38f7b83035"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# LLM_OUTPUT_QUARANTINE_PATTERN
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::LLM_OUTPUT_QUARANTINE_PATTERN::5689ca38f7b83035`

## Description
All LLM output enters the graph as an unverified entity at the lowest trust zone (SOURCE_CLAIM at A2_HIGH_INTAKE). Must pass all deterministic gates to advance. LLM never moves an entity — graph logic does.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[MODEL_SELECTOR_PREFERS_NO_LLM]]

## Inward Relations
- [[JP_DETERMINISM_PRINCIPLE_MATERIALIZED.md]] → **ENGINE_PATTERN_PASS**
