---
id: "SKILL::sim-engine"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# sim-engine
**Node ID:** `SKILL::sim-engine`

## Description
SIM stress testing, evidence, kills

## Properties
- **skill_type**: verification
- **source_type**: operator_module
- **source_path**: system_v4/skills/sim_engine.py
- **status**: active
- **applicable_layers**: ["SIM_EVIDENCED"]
- **applicable_trust_zones**: ["SIM_EVIDENCED"]
- **applicable_graphs**: ["runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/sim_engine.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[sim_7_tier_architecture]]
- **SKILL_OPERATES_ON** → [[evidence_ladder_sims]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]

## Inward Relations
- [[graveyard-lawyer]] → **RELATED_TO**
