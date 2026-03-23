---
id: "A2_3::ENGINE_PATTERN_PASS::GRAVEYARD_RESCUE_FRACTION::3ec64bfdc8439602"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# GRAVEYARD_RESCUE_FRACTION
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::GRAVEYARD_RESCUE_FRACTION::3ec64bfdc8439602`

## Description
Autowiggle allocates a configurable fraction of strategy targets (default ~50% when graveyard is non-empty) to RESCUE operations, pulling killed items back from the graveyard for re-evaluation. The graveyard is not a trash can — it is a dependency-aware staging area.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[graveyard_rescue_share]]
- **RELATED_TO** → [[Graveyard_Mandatory_Never_Dead]]

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
