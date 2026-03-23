---
id: "SKILL::a2-a1-memory-admission-guard"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-a1-memory-admission-guard
**Node ID:** `SKILL::a2-a1-memory-admission-guard`

## Description
Guard what enters persistent memory

## Properties
- **skill_type**: verification
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-a1-memory-admission-guard/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A1_JARGONED"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A1_JARGONED"]
- **applicable_graphs**: ["concept"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/a2-a1-memory-admission-guard/SKILL.md", "gemini": "system_v4/skill_specs/a2-a1-memory-admission-guard/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a2_canonical_schemas]]
- **SKILL_OPERATES_ON** → [[four_layer_trust_architecture]]

## Inward Relations
- [[memory-admission-guard]] → **RELATED_TO**
