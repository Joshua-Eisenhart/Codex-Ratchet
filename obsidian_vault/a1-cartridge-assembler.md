---
id: "SKILL::a1-cartridge-assembler"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-cartridge-assembler
**Node ID:** `SKILL::a1-cartridge-assembler`

## Description
Package A1 candidates into ratchet cartridges

## Properties
- **skill_type**: orchestration
- **source_type**: operator_module
- **source_path**: system_v4/skills/a1_cartridge_assembler.py
- **status**: active
- **applicable_layers**: ["A1_CARTRIDGE", "PHASE_A1_CARTRIDGE"]
- **applicable_trust_zones**: ["A1_CARTRIDGE", "PHASE_A1_CARTRIDGE"]
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a1_cartridge_assembler.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a1_strategy_v1_schema]]

## Inward Relations
- [[a1-cartridge-graph-builder]] → **RELATED_TO**
