---
id: "SKILL::identity-registry-overlap-quarantine"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# identity-registry-overlap-quarantine
**Node ID:** `SKILL::identity-registry-overlap-quarantine`

## Description
Quarantine heuristic identity-overlap edges out of the live identity owner surface into a separate non-canonical suggestion surface, keeping the owner graph limited to canonical identity facts.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/identity-registry-overlap-quarantine/SKILL.md
- **status**: active
- **applicable_layers**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_trust_zones**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_graphs**: ["concept", "rosetta", "dependency"]
- **inputs**: ["identity_registry_v1"]
- **outputs**: ["identity_registry_v1", "identity_registry_overlap_suggestions_v1", "identity_registry_overlap_quarantine_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/identity-registry-overlap-quarantine/SKILL.md", "gemini": "system_v4/skill_specs/identity-registry-overlap-quarantine/SKILL.md", "shell": "system_v4/skills/identity_re
- **related_skills**: ["identity-registry-builder", "graph-capability-auditor", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[identity-registry-builder]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **SKILL_OPERATES_ON** → [[KERNEL__IDENTITY_EMERGENCE]]
