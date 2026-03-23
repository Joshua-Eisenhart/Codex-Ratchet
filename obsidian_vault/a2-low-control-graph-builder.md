---
id: "SKILL::a2-low-control-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-low-control-graph-builder
**Node ID:** `SKILL::a2-low-control-graph-builder`

## Description
Materialize the bounded A2 low-control owner graph from the live refinery graph after the upstream A2 owner graphs exist.

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-low-control-graph-builder/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "PHASE_A2_1_PROMOTION"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "PHASE_A2_1_PROMOTION"]
- **applicable_graphs**: ["dependency"]
- **inputs**: ["system_graph_a2_refinery", "identity_registry_v1", "a2_high_intake_graph_v1", "a2_mid_refinement_graph_v1"]
- **outputs**: ["a2_low_control_graph_v1", "a2_low_control_graph_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-low-control-graph-builder/SKILL.md", "gemini": "system_v4/skill_specs/a2-low-control-graph-builder/SKILL.md", "shell": "system_v4/skills/a2_low_control_graph_builde
- **related_skills**: ["identity-registry-builder", "a2-high-intake-graph-builder", "a2-mid-refinement-graph-builder", "graph-capability-auditor", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[identity-registry-builder]]
- **RELATED_TO** → [[a2-high-intake-graph-builder]]
- **RELATED_TO** → [[a2-mid-refinement-graph-builder]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]
- **SKILL_OPERATES_ON** → [[GRAPH_AS_CONTROL_SUBSTRATE]]

## Inward Relations
- [[a1-jargoned-graph-builder]] → **RELATED_TO**
