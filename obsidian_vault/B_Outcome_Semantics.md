---
id: "A2_3::ENGINE_PATTERN_PASS::B_Outcome_Semantics::eac6f931b0928d3e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# B_Outcome_Semantics
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::B_Outcome_Semantics::eac6f931b0928d3e`

## Description
ACCEPT: append survivor order, mutate canon state. PARK: not admitted, retained for replay/unpark. REJECT: not admitted, write graveyard record.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **EXCLUDES** → [[b_kernel_outcome_semantics]]

## Inward Relations
- [[03_B_KERNEL_SPEC.md]] → **ENGINE_PATTERN_PASS**
- [[B_Graveyard_Write_Contract]] → **RELATED_TO**
