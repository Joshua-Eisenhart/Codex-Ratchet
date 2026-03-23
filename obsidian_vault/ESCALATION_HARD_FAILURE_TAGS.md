---
id: "A2_3::ENGINE_PATTERN_PASS::ESCALATION_HARD_FAILURE_TAGS::52a869e53ac9d399"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# ESCALATION_HARD_FAILURE_TAGS
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::ESCALATION_HARD_FAILURE_TAGS::52a869e53ac9d399`

## Description
5 hard failure tags trigger escalation: SCHEMA_FAIL, UNDEFINED_TERM_USE, DERIVED_ONLY_PRIMITIVE_USE, DERIVED_ONLY_NOT_PERMITTED, SPEC_KIND_UNSUPPORTED. If ≥3 consecutive rejects all carry hard tags, or generation/schema fail limits are exceeded, the system escalates rather than retrying.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_model_selector.py]] → **ENGINE_PATTERN_PASS**
