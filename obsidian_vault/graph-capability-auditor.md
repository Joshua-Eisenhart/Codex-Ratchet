---
id: "SKILL::graph-capability-auditor"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# graph-capability-auditor
**Node ID:** `SKILL::graph-capability-auditor`

## Description
Audit what the current graph substrate can actually express and what it still cannot.

## Properties
- **skill_type**: audit
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/graph-capability-auditor/SKILL.md
- **status**: active
- **applicable_layers**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_trust_zones**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_graphs**: ["concept", "dependency", "rosetta", "runtime", "attractor"]
- **inputs**: ["system_graph_a2_refinery", "nested_graph_v1", "promoted_subgraph", "a1_graph_projection"]
- **outputs**: ["graph_capability_report", "graph_capability_note"]
- **adapters**: {"codex": "system_v4/skill_specs/graph-capability-auditor/SKILL.md", "gemini": "system_v4/skill_specs/graph-capability-auditor/SKILL.md", "shell": "system_v4/skills/graph_capability_auditor.py"}
- **related_skills**: ["ratchet-a2-a1", "nested-graph-layer-auditor", "ratchet-overseer"]

## Outward Relations
- **RELATED_TO** → [[ratchet-a2-a1]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[ratchet-overseer]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[a1-cartridge-graph-builder]] → **RELATED_TO**
- [[a1-entropy-bridge-helper-lift-pack]] → **RELATED_TO**
- [[a1-entropy-diversity-alias-lift-pack]] → **RELATED_TO**
- [[a1-entropy-structure-decomposition-control]] → **RELATED_TO**
- [[a1-first-entropy-structure-campaign]] → **RELATED_TO**
- [[a1-jargoned-graph-builder]] → **RELATED_TO**
- [[a1-stripped-exact-term-aligner]] → **RELATED_TO**
- [[a1-stripped-term-plan-aligner]] → **RELATED_TO**
- [[a2-colder-witness-execution-consolidation]] → **RELATED_TO**
- [[a2-entropy-bridge-helper-decomposition-control]] → **RELATED_TO**
- [[a2-high-intake-graph-builder]] → **RELATED_TO**
- [[a2-low-control-graph-builder]] → **RELATED_TO**
- [[a2-mid-refinement-graph-builder]] → **RELATED_TO**
- [[a2-refinement-for-a1-stripped-landing]] → **RELATED_TO**
- [[a2-stage1-operatorized-entropy-head-refinement]] → **RELATED_TO**
- [[a2-substrate-base-queue-pivot-audit]] → **RELATED_TO**
- [[identity-registry-builder]] → **RELATED_TO**
- [[identity-registry-overlap-quarantine]] → **RELATED_TO**
- [[nested-graph-layer-auditor]] → **RELATED_TO**
- [[a2-brain-surface-refresher]] → **RELATED_TO**
- [[a2-skill-improver-readiness-operator]] → **RELATED_TO**
