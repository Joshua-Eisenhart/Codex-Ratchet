---
id: "SKILL::a2-substrate-base-queue-pivot-audit"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-substrate-base-queue-pivot-audit
**Node ID:** `SKILL::a2-substrate-base-queue-pivot-audit`

## Description
Audit whether the dormant substrate-base family slice should replace the current entropy-selected A1 queue candidate, and update the live current A1 queue surfaces only if the existing queue selector admits it.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-substrate-base-queue-pivot-audit/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL"]
- **applicable_graphs**: ["concept", "dependency"]
- **inputs**: ["current_a1_queue_packet", "current_a1_candidate_registry", "substrate_base_family_slice", "substrate_family_campaign", "queue_status_surface_spec"]
- **outputs**: ["substrate_base_queue_pivot_audit", "current_a1_candidate_registry", "current_a1_queue_packet", "current_a1_queue_note"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-substrate-base-queue-pivot-audit/SKILL.md", "gemini": "system_v4/skill_specs/a2-substrate-base-queue-pivot-audit/SKILL.md", "shell": "system_v4/skills/a2_substrate_
- **related_skills**: ["graph-capability-auditor", "nested-graph-layer-auditor", "a1-jargoned-graph-builder"]

## Outward Relations
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[a1-jargoned-graph-builder]]
