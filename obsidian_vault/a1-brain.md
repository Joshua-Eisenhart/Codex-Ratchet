---
id: "SKILL::a1-brain"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-brain
**Node ID:** `SKILL::a1-brain`

## Description
A1 extraction, classification, routing

## Properties
- **skill_type**: extraction
- **source_type**: operator_module
- **source_path**: system_v4/skills/a1_brain.py
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_graphs**: ["rosetta", "dependency"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a1_brain.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a1_rosetta_function]]
- **SKILL_OPERATES_ON** → [[a1_strategy_v1_schema]]
- **SKILL_OPERATES_ON** → [[a1_thread_boot_eight_hard_rules]]
- **SKILL_OPERATES_ON** → [[TERM_RATCHET_THROUGH_EVIDENCE]]

## Inward Relations
- [[wiggle-lane-runner]] → **RELATED_TO**
