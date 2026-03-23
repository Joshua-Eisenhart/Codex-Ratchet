---
id: "A2_3::SOURCE_MAP_PASS::runtime_image_policy::1097de3567456a1f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# runtime_image_policy
**Node ID:** `A2_3::SOURCE_MAP_PASS::runtime_image_policy::1097de3567456a1f`

## Description
Runtime memory discipline. Persistent directories allowed: canonical_ledger/, snapshots/, current_state/, cache/. Cache is derived and deletable.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]
- **EXCLUDES** → [[runtime_image_policy_v1]]

## Inward Relations
- [[RUNTIME_IMAGE_POLICY_v1.md]] → **SOURCE_MAP_PASS**
- [[governance_and_anti_pattern_policies]] → **DEPENDS_ON**
- [[control_plane_runtime_image_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v2_runtime_image_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v3_runtime_image_policy_v1]] → **DEPENDS_ON**
- [[sysrepair_v4_runtime_image_policy_v1]] → **DEPENDS_ON**
