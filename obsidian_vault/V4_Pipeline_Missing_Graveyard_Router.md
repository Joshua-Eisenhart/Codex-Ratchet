---
id: "A2_3::ENGINE_PATTERN_PASS::V4_Pipeline_Missing_Graveyard_Router::26bc9fb4f616cdc5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# V4_Pipeline_Missing_Graveyard_Router
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::V4_Pipeline_Missing_Graveyard_Router::26bc9fb4f616cdc5`

## Description
Current gap: when B issues REJECT or SIM fails, the items need to be routed to a GRAVEYARD with their sim evidence attached. The graveyard is NOT a trash heap — items carry their full failure evidence and sim results. A graveyard router needs to: (1) capture failure reason, (2) attach sim evidence, (3) link to the survivor that beat them, (4) remain queryable for resurrection by A1.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[Base constraints ledger v1.md]] → **ENGINE_PATTERN_PASS**
