---
id: "SKILL::a1-routing-state"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-routing-state
**Node ID:** `SKILL::a1-routing-state`

## Description
A1 treatment traces and pass tracking

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a1_routing_state.py
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a1_routing_state.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
