---
id: "SKILL::a1-distiller"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-distiller
**Node ID:** `SKILL::a1-distiller`

## Description
Distill A2 concepts → A1 kernel candidates

## Properties
- **skill_type**: extraction
- **source_type**: operator_module
- **source_path**: system_v4/skills/a1_distiller.py
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_graphs**: ["dependency"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a1_distiller.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
