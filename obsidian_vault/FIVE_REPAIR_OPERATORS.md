---
id: "A2_3::ENGINE_PATTERN_PASS::FIVE_REPAIR_OPERATORS::7996f42f0298fa96"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# FIVE_REPAIR_OPERATORS
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::FIVE_REPAIR_OPERATORS::7996f42f0298fa96`

## Description
A0 compiler applies 5 deterministic repair operators to strategies before emitting export blocks: OP_INJECT_PROBE (adds missing probes), OP_REORDER_DEPENDENCIES (topological sort), OP_MUTATE_LEXEME (L0/L1 token substitution), OP_REPAIR_DEF_FIELD (schema fixes), OP_NEG_SIM_EXPAND (negative class expansion).

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a0_compiler.py]] → **ENGINE_PATTERN_PASS**
- [[A1_Repair_Operators]] → **STRUCTURALLY_RELATED**
