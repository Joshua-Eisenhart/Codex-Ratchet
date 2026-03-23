---
id: "SKILL::a2-brain-refresh"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-brain-refresh
**Node ID:** `SKILL::a2-brain-refresh`

## Description
Refresh A2 brain state from graph

## Properties
- **skill_type**: maintenance
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-brain-refresh/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["concept"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/a2-brain-refresh/SKILL.md", "gemini": "system_v4/skill_specs/a2-brain-refresh/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[a2_canonical_schemas]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[external-research-refinery-launcher]] → **RELATED_TO**
- [[a2-brain-surface-refresher]] → **RELATED_TO**
