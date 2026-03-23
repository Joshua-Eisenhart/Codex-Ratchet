---
id: "A2_3::ENGINE_PATTERN_PASS::JP_DETERMINISM_FIRST_RULE::166257bb26b979bc"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# JP_DETERMINISM_FIRST_RULE
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::JP_DETERMINISM_FIRST_RULE::166257bb26b979bc`

## Description
Entities and lifecycles move deterministically through a graph. LLMs/agents do inference tasks only. Determinism is always preferred. 2 of 3 strategy sources in Ratchet (autowiggle, replay) run without any LLM.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[topological_reasoning_runtime]]
- **RELATED_TO** → [[reference_repos_catalog]]
- **RELATED_TO** → [[MODEL_SELECTOR_PREFERS_NO_LLM]]

## Inward Relations
- [[JP_DETERMINISM_PRINCIPLE_MATERIALIZED.md]] → **ENGINE_PATTERN_PASS**
- [[FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM]] → **RELATED_TO**
- [[lev_skill_system]] → **RELATED_TO**
