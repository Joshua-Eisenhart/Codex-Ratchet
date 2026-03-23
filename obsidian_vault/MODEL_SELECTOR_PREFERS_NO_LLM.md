---
id: "A2_3::ENGINE_PATTERN_PASS::MODEL_SELECTOR_PREFERS_NO_LLM::8418792169137851"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# MODEL_SELECTOR_PREFERS_NO_LLM
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::MODEL_SELECTOR_PREFERS_NO_LLM::8418792169137851`

## Description
a1_model_selector ranks benchmark results by: needs_real_llm (prefer FALSE) → id_churn_signal (prefer FALSE) → rejected_total (minimize) → parked_total (minimize) → accepted_total (maximize). Models that don't need an actual LLM are always ranked first.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[THREE_SOURCE_MULTIPLEXER]]

## Inward Relations
- [[a1_model_selector.py]] → **ENGINE_PATTERN_PASS**
- [[JP_DETERMINISM_FIRST_RULE]] → **RELATED_TO**
- [[LLM_OUTPUT_QUARANTINE_PATTERN]] → **RELATED_TO**
