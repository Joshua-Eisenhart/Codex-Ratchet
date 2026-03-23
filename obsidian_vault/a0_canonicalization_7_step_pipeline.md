---
id: "A2_3::SOURCE_MAP_PASS::a0_canonicalization_7_step_pipeline::f20495838a1a0e8d"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# a0_canonicalization_7_step_pipeline
**Node ID:** `A2_3::SOURCE_MAP_PASS::a0_canonicalization_7_step_pipeline::f20495838a1a0e8d`

## Description
A0 canonicalization: parse strategy, drop forbidden fields (confidence/probability/embedding), normalize scalar types, sort object keys, normalize list ordering, serialize canonical JSON, hash to strategy_hash. Deterministic and reproducible.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[a0_deterministic_canonicalization]]
- **RELATED_TO** → [[a0_deterministic_compilation_contract]]
- **RELATED_TO** → [[a0_export_block_grammar_compiler]]

## Inward Relations
- [[04_A0_COMPILER_SPEC.md]] → **SOURCE_MAP_PASS**
- [[A0_Canonicalization_Pipeline]] → **STRUCTURALLY_RELATED**
