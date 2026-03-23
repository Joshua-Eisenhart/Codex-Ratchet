---
id: "SKILL::a2-mid-refinement-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-mid-refinement-graph-builder
**Node ID:** `SKILL::a2-mid-refinement-graph-builder`

## Description
Materialize the bounded A2 mid-refinement owner graph from the live refinery graph after the identity and A2 high-intake owner graphs exist.

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-mid-refinement-graph-builder/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "PHASE_A2_2_CONTRADICTION"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "PHASE_A2_2_CONTRADICTION"]
- **applicable_graphs**: ["concept"]
- **inputs**: ["system_graph_a2_refinery", "identity_registry_v1", "a2_high_intake_graph_v1"]
- **outputs**: ["a2_mid_refinement_graph_v1", "a2_mid_refinement_graph_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-mid-refinement-graph-builder/SKILL.md", "gemini": "system_v4/skill_specs/a2-mid-refinement-graph-builder/SKILL.md", "shell": "system_v4/skills/a2_mid_refinement_gra
- **related_skills**: ["identity-registry-builder", "a2-high-intake-graph-builder", "graph-capability-auditor", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[identity-registry-builder]]
- **RELATED_TO** → [[a2-high-intake-graph-builder]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]

## Inward Relations
- [[a2-low-control-graph-builder]] → **RELATED_TO**
- [[a2-refinement-for-a1-stripped-landing]] → **RELATED_TO**
