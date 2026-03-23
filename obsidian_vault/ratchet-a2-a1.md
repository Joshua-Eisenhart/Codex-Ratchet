---
id: "SKILL::ratchet-a2-a1"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-a2-a1
**Node ID:** `SKILL::ratchet-a2-a1`

## Description
A2→A1 distillation pipeline

## Properties
- **skill_type**: orchestration
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/ratchet-a2-a1/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A1_JARGONED", "A1_STRIPPED"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A1_JARGONED", "A1_STRIPPED"]
- **applicable_graphs**: ["provenance", "concept", "rosetta", "dependency"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"codex": "~/.codex/skills/ratchet-a2-a1/SKILL.md", "gemini": "system_v4/skill_specs/ratchet-a2-a1/SKILL.md"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[A2_TO_B_DETERMINISTIC_BRIDGE]]

## Inward Relations
- [[graph-capability-auditor]] → **RELATED_TO**
- [[identity-registry-builder]] → **RELATED_TO**
- [[nested-graph-layer-auditor]] → **RELATED_TO**
