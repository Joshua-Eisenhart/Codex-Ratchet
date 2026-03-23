---
id: "SKILL::v4-tape-writer"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# v4-tape-writer
**Node ID:** `SKILL::v4-tape-writer`

## Description
Write campaign/evidence tapes

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/v4_tape_writer.py
- **status**: active
- **applicable_layers**: ["SIM_EVIDENCED"]
- **applicable_trust_zones**: ["SIM_EVIDENCED"]
- **applicable_graphs**: ["runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/v4_tape_writer.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
