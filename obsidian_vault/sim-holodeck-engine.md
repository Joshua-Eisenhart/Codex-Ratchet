---
id: "SKILL::sim-holodeck-engine"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# sim-holodeck-engine
**Node ID:** `SKILL::sim-holodeck-engine`

## Description
Holodeck scenario engine

## Properties
- **skill_type**: orchestration
- **source_type**: operator_module
- **source_path**: system_v4/skills/sim_holodeck_engine.py
- **status**: active
- **applicable_layers**: ["HOLODECK_MEMORY"]
- **applicable_trust_zones**: ["HOLODECK_MEMORY"]
- **applicable_graphs**: ["memory"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/sim_holodeck_engine.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[sim_7_tier_architecture]]
- **SKILL_OPERATES_ON** → [[evidence_ladder_sims]]
