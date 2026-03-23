---
id: "A2_3::ENGINE_PATTERN_PASS::A0_Budget_Enforcement::b7ce9b0e2b8599cd"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# A0_Budget_Enforcement
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::A0_Budget_Enforcement::b7ce9b0e2b8599cd`

## Description
Budgets: max_items, max_sims, max_wall_ms. Overflow uses deterministic truncation: drop lowest-priority bucket first, then reverse lexical order, then highest dependency depth, then latest branch id.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[a0_budget_truncation]]

## Inward Relations
- [[04_A0_COMPILER_SPEC.md]] → **ENGINE_PATTERN_PASS**
