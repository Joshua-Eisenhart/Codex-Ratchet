---
id: "SKILL::a1-rosetta-mapper"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-rosetta-mapper
**Node ID:** `SKILL::a1-rosetta-mapper`

## Description
Map overlay labels to Rosetta aliases

## Properties
- **skill_type**: refinement
- **source_type**: operator_module
- **source_path**: system_v4/skills/a1_rosetta_mapper.py
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "PHASE_A1_ROSETTA"]
- **applicable_trust_zones**: ["A1_JARGONED", "PHASE_A1_ROSETTA"]
- **applicable_graphs**: ["rosetta"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a1_rosetta_mapper.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a1_rosetta_function]]
