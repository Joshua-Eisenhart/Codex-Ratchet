---
id: "A2_3::ENGINE_PATTERN_PASS::THREE_SOURCE_MULTIPLEXER::d25a2c6079d85020"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# THREE_SOURCE_MULTIPLEXER
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::THREE_SOURCE_MULTIPLEXER::d25a2c6079d85020`

## Description
A1Bridge multiplexes between 3 strategy sources: REPLAY (deterministic template rotation — no LLM), PACKET (ZIP inbox consumption — may involve LLM output), AUTOWIGGLE (deterministic branchy generation — no LLM). This means 2 of 3 modes run entirely without LLM contact.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_model_selector.py]] → **ENGINE_PATTERN_PASS**
- [[MODEL_SELECTOR_PREFERS_NO_LLM]] → **RELATED_TO**
