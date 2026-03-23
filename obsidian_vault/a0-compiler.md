---
id: "SKILL::a0-compiler"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a0-compiler
**Node ID:** `SKILL::a0-compiler`

## Description
Compile deterministic execution blocks

## Properties
- **skill_type**: bridge
- **source_type**: operator_module
- **source_path**: system_v4/skills/a0_compiler.py
- **status**: active
- **applicable_layers**: ["A0_COMPILED"]
- **applicable_trust_zones**: ["A0_COMPILED"]
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/a0_compiler.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a0_deterministic_canonicalization]]
- **SKILL_OPERATES_ON** → [[a0_export_block_compilation]]
