---
id: "SKILL::a1-from-a2-distillation"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-from-a2-distillation
**Node ID:** `SKILL::a1-from-a2-distillation`

## Description
A1 distillation from A2 candidates

## Properties
- **skill_type**: extraction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-from-a2-distillation/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_graphs**: ["concept", "dependency"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/a1-from-a2-distillation/SKILL.md", "gemini": "system_v4/skill_specs/a1-from-a2-distillation/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
