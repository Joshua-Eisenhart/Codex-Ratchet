---
id: "SKILL::automation-controller"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# automation-controller
**Node ID:** `SKILL::automation-controller`

## Description
Codex automation orchestration

## Properties
- **skill_type**: orchestration
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/automation-controller/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: []
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/codex-automation-controller/SKILL.md", "gemini": "system_v4/skill_specs/automation-controller/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[run-real-ratchet]]
- **SKILL_OPERATES_ON** → [[a2_controller_dispatch_first]]
