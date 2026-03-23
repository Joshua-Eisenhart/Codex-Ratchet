---
id: "A2_3::SOURCE_MAP_PASS::layer_transport_boundaries::cf52a36025a0e972"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# layer_transport_boundaries
**Node ID:** `A2_3::SOURCE_MAP_PASS::layer_transport_boundaries::cf52a36025a0e972`

## Description
Hard boundaries defining cross-layer artifacts. A2 emits PROPOSAL to A1. A1 emits STRATEGY to A0. A0 emits EXPORT_BATCH to B. B emits STATE_UPDATE to A0. SIM emits SIM_RESULT to A0.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_02_layer_boundaries]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_02_layer_boundaries]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_02_layer_boundaries]]

## Inward Relations
- [[02_LAYER_BOUNDARIES.md]] → **SOURCE_MAP_PASS**
- [[artifact_invariants]] → **RELATED_TO**
- [[control_plane_02_layer_boundaries]] → **STRUCTURALLY_RELATED**
- [[layer_boundaries]] → **STRUCTURALLY_RELATED**
- [[02_layer_boundaries]] → **STRUCTURALLY_RELATED**
