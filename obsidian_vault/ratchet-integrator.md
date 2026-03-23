---
id: "SKILL::ratchet-integrator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-integrator
**Node ID:** `SKILL::ratchet-integrator`

## Description
Write ratchet outcomes into graph

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/ratchet_integrator.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "B_ADJUDICATED"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "B_ADJUDICATED"]
- **applicable_graphs**: ["runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/ratchet_integrator.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[unitary_thread_b_ratchet]]
- **SKILL_OPERATES_ON** → [[COUPLED_LADDER_RATCHET]]
