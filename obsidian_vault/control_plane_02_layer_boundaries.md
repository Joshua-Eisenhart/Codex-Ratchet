---
id: "A2_3::SOURCE_MAP_PASS::control_plane_02_layer_boundaries::2ce0e1499c59b5ac"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# control_plane_02_layer_boundaries
**Node ID:** `A2_3::SOURCE_MAP_PASS::control_plane_02_layer_boundaries::2ce0e1499c59b5ac`

## Description
02_LAYER_BOUNDARIES.md (1407B):  # Layer Boundaries  This document defines the **hard boundaries** between layers and which artifacts may cross each boundary.  ## Boundary: A2 → A1 Allowed: - `A2_TO_A1_PROPOSAL_ZIP` (FORWARD) Forbidden: - Any mutation container (`EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2`) - 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[sim_evidence]]
- **DEPENDS_ON** → [[layer_boundaries]]
- **DEPENDS_ON** → [[sim_evidence_v1]]
- **DEPENDS_ON** → [[02_layer_boundaries]]
- **DEPENDS_ON** → [[thread_s_save_snapshot_v2]]
- **DEPENDS_ON** → [[export_block]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_02_layer_boundaries]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_02_layer_boundaries]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_02_layer_boundaries]]
- **STRUCTURALLY_RELATED** → [[layer_transport_boundaries]]

## Inward Relations
- [[00_README.md]] → **SOURCE_MAP_PASS**
- [[02_layer_boundaries]] → **STRUCTURALLY_RELATED**
