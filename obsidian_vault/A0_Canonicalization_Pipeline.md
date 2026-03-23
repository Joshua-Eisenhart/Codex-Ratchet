---
id: "A2_3::ENGINE_PATTERN_PASS::A0_Canonicalization_Pipeline::7a9c0afff1c2577c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# A0_Canonicalization_Pipeline
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::A0_Canonicalization_Pipeline::7a9c0afff1c2577c`

## Description
Parse strategy -> drop forbidden fields (confidence, probability, embedding) -> normalize scalars -> sort keys -> normalize list ordering -> serialize canonical JSON -> hash. Outputs: strategy_canonical.json, strategy_hash.txt.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[a0_canonicalization_7_step_pipeline]]

## Inward Relations
- [[04_A0_COMPILER_SPEC.md]] → **ENGINE_PATTERN_PASS**
