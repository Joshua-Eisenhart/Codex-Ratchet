---
id: "A2_3::SOURCE_MAP_PASS::a1_repair_operator_mapping::f32003ef327f0146"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# a1_repair_operator_mapping
**Node ID:** `A2_3::SOURCE_MAP_PASS::a1_repair_operator_mapping::f32003ef327f0146`

## Description
Defines the allowed operator space for A1 repair based on failure classes (SIM-driven or Compiler-style). Requires operator exhaustion before A2 escalation. Enforces anti-fake wiggle constraints.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[control_plane_a1_repair_operator_mapping_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v2_a1_repair_operator_mapping_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v3_a1_repair_operator_mapping_v1]]
- **STRUCTURALLY_RELATED** → [[sysrepair_v4_a1_repair_operator_mapping_v1]]
- **STRUCTURALLY_RELATED** → [[a1_repair_operator_mapping_v1]]
- **DEPENDS_ON** → [[constraints]]

## Inward Relations
- [[A1_REPAIR_OPERATOR_MAPPING_v1.md]] → **SOURCE_MAP_PASS**
- [[a1_owner_scope_live_vs_legacy]] → **DEPENDS_ON**
- [[a1_strategy_schema_and_repair]] → **DEPENDS_ON**
- [[control_plane_a1_repair_operator_mapping_v1]] → **DEPENDS_ON**
- [[a1_owner_scope_live_vs_legacy]] → **DEPENDS_ON**
