---
id: "SKILL::a1-cartridge-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-cartridge-graph-builder
**Node ID:** `SKILL::a1-cartridge-graph-builder`

## Description
Materialize the bounded A1 cartridge owner graph from the live A1 stripped owner graph and current cartridge doctrine, or fail closed if only witness-side stripped terms are present.

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-cartridge-graph-builder/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_CARTRIDGE"]
- **applicable_trust_zones**: ["A1_CARTRIDGE"]
- **applicable_graphs**: ["strategy"]
- **inputs**: ["a1_stripped_graph_v1", "a1_cartridge_review", "a1_cartridge_cross_judgment", "a1_entropy_diversity_alias_lift_pack"]
- **outputs**: ["a1_cartridge_graph_v1", "a1_cartridge_graph_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a1-cartridge-graph-builder/SKILL.md", "gemini": "system_v4/skill_specs/a1-cartridge-graph-builder/SKILL.md", "shell": "system_v4/skills/a1_cartridge_graph_builder.py"}
- **related_skills**: ["a1-stripped-graph-builder", "a1-cartridge-assembler", "nested-graph-layer-auditor", "graph-capability-auditor"]

## Outward Relations
- **RELATED_TO** → [[a1-stripped-graph-builder]]
- **RELATED_TO** → [[a1-cartridge-assembler]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **SKILL_OPERATES_ON** → [[a1_strategy_v1_schema]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]

## Inward Relations
- [[a1-stripped-exact-term-aligner]] → **RELATED_TO**
- [[a1-stripped-term-plan-aligner]] → **RELATED_TO**
