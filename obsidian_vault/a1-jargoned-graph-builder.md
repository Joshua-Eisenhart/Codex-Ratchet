---
id: "SKILL::a1-jargoned-graph-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a1-jargoned-graph-builder
**Node ID:** `SKILL::a1-jargoned-graph-builder`

## Description
Materialize the bounded A1 jargoned owner graph from packet-backed Rosetta fuel, or fail closed when the queued A1 scope does not align with live Rosetta anchors.

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a1-jargoned-graph-builder/SKILL.md
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "PHASE_A1_ROSETTA"]
- **applicable_trust_zones**: ["A1_JARGONED", "PHASE_A1_ROSETTA"]
- **applicable_graphs**: ["rosetta"]
- **inputs**: ["system_graph_a2_refinery", "rosetta_v2", "a1_queue_candidate_registry", "a2_to_a1_family_slice"]
- **outputs**: ["a1_jargoned_graph_v1", "a1_jargoned_graph_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a1-jargoned-graph-builder/SKILL.md", "gemini": "system_v4/skill_specs/a1-jargoned-graph-builder/SKILL.md", "shell": "system_v4/skills/a1_jargoned_graph_builder.py"}
- **related_skills**: ["identity-registry-builder", "a2-low-control-graph-builder", "graph-capability-auditor", "nested-graph-layer-auditor", "a1-rosetta-stripper"]

## Outward Relations
- **RELATED_TO** → [[identity-registry-builder]]
- **RELATED_TO** → [[a2-low-control-graph-builder]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[a1-rosetta-stripper]]

## Inward Relations
- [[a1-jargoned-scope-aligner]] → **RELATED_TO**
- [[a1-stripped-graph-builder]] → **RELATED_TO**
- [[a2-substrate-base-queue-pivot-audit]] → **RELATED_TO**
