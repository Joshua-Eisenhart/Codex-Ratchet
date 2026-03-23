---
id: "A2_3::ENGINE_PATTERN_PASS::FORBIDDEN_CONTAINER_ISOLATION::0e8beb6605e62c7c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# FORBIDDEN_CONTAINER_ISOLATION
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::FORBIDDEN_CONTAINER_ISOLATION::0e8beb6605e62c7c`

## Description
Each ZIP type has a forbidden container set. Export ZIPs forbid SIM_EVIDENCE and SNAPSHOT. SIM ZIPs forbid EXPORT_BLOCK and SNAPSHOT. Save ZIPs forbid all mutation containers. This prevents layer-crossing contamination.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[zip_protocol_v2_validator.py]] → **ENGINE_PATTERN_PASS**
