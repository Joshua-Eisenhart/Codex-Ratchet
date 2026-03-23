---
id: "SKILL::a1-stripped-term-plan-aligner"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-stripped-term-plan-aligner
**Node ID:** `SKILL::a1-stripped-term-plan-aligner`

## Description
Resolve whether a bounded passenger family term has any honest exact stripped landing under current repo-held doctrine, emit an explicit audit, and keep A1 fail-closed when no exact landing exists.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-stripped-term-plan-aligner/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: ["dependency"]
- **inputs**: ["a1_jargoned_graph_v1", "a1_stripped_graph_v1", "a1_cartridge_graph_v1", "a1_family_doctrine_surfaces"]
- **outputs**: ["a1_stripped_term_plan_alignment_audit", "a1_stripped_graph_v1", "a1_cartridge_graph_v1"]
- **adapters**: {"codex": "system_v4/skill_specs/a1-stripped-term-plan-aligner/SKILL.md", "gemini": "system_v4/skill_specs/a1-stripped-term-plan-aligner/SKILL.md", "shell": "system_v4/skills/a1_stripped_term_plan_ali
- **related_skills**: ["a1-stripped-graph-builder", "a1-stripped-exact-term-aligner", "a1-cartridge-graph-builder", "nested-graph-layer-auditor", "graph-capability-auditor"]

## Outward Relations
- **RELATED_TO** → [[a1-stripped-graph-builder]]
- **RELATED_TO** → [[a1-stripped-exact-term-aligner]]
- **RELATED_TO** → [[a1-cartridge-graph-builder]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[graph-capability-auditor]]

## Inward Relations
- [[a2-refinement-for-a1-stripped-landing]] → **RELATED_TO**
