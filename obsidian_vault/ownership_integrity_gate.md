---
id: "A2_3::SOURCE_MAP_PASS::ownership_integrity_gate::ed412b4305560d8a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# ownership_integrity_gate
**Node ID:** `A2_3::SOURCE_MAP_PASS::ownership_integrity_gate::ed412b4305560d8a`

## Description
Guards that exactly one document owns each requirement ID natively. Non-owners may cross-reference but never redefine or overwrite semantic intent.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[ownership_map_single_owner_rule]]
- **DEPENDS_ON** → [[reference]]

## Inward Relations
- [[09_CONFORMANCE_AND_REDUNDANCY_GATES.md]] → **SOURCE_MAP_PASS**
