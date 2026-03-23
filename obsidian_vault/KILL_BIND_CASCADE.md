---
id: "A2_3::ENGINE_PATTERN_PASS::KILL_BIND_CASCADE::68444626f33bcfce"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# KILL_BIND_CASCADE
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::KILL_BIND_CASCADE::68444626f33bcfce`

## Description
When a negative SIM kills a spec, KILL_BIND propagates the kill to all bound math artifacts. The bound artifact also enters the graveyard. Interaction counts exclude killed specs.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[test_negative_sim_semantics.py]] → **ENGINE_PATTERN_PASS**
