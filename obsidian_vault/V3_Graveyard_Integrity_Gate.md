---
id: "A2_3::ENGINE_PATTERN_PASS::V3_Graveyard_Integrity_Gate::f4ba697211ec8683"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# V3_Graveyard_Integrity_Gate
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::V3_Graveyard_Integrity_Gate::f4ba697211ec8683`

## Description
V3 run_graveyard_integrity_gate.py: validates graveyard records have required keys (candidate_id, reason_tag, raw_lines, failure_class). Failure_class must be B_KILL or SIM_KILL. Minimum record count enforced. This is a quality gate — the graveyard must be well-formed or the run fails.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[kernel.py]] → **ENGINE_PATTERN_PASS**
