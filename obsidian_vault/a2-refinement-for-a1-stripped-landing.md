---
id: "SKILL::a2-refinement-for-a1-stripped-landing"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-refinement-for-a1-stripped-landing
**Node ID:** `SKILL::a2-refinement-for-a1-stripped-landing`

## Description
Run one bounded A2-only correction pass for a stalled direct-structure target whose A1 stripped landing failed closed, and write an explicit audit that either names a current source-anchored landing or preserves the blocker.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-refinement-for-a1-stripped-landing/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: ["concept"]
- **inputs**: ["a1_stripped_graph_v1", "a1_stripped_term_plan_alignment_audit", "a2_stage1_entropy_head_doctrine"]
- **outputs**: ["a2_refinement_for_a1_stripped_landing_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-refinement-for-a1-stripped-landing/SKILL.md", "gemini": "system_v4/skill_specs/a2-refinement-for-a1-stripped-landing/SKILL.md", "shell": "system_v4/skills/a2_refine
- **related_skills**: ["a2-mid-refinement-graph-builder", "a1-stripped-term-plan-aligner", "graph-capability-auditor", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[a2-mid-refinement-graph-builder]]
- **RELATED_TO** → [[a1-stripped-term-plan-aligner]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]

## Inward Relations
- [[a2-stage1-operatorized-entropy-head-refinement]] → **RELATED_TO**
