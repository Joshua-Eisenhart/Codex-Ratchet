---
id: "SKILL::identity-registry-builder"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# identity-registry-builder
**Node ID:** `SKILL::identity-registry-builder`

## Description
Build the first additive identity-registry scaffold from the live refinery graph without pretending the full nested stack already exists.

## Properties
- **skill_type**: refinement
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/identity-registry-builder/SKILL.md
- **status**: active
- **applicable_layers**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_trust_zones**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_graphs**: ["concept", "rosetta", "dependency"]
- **inputs**: ["system_graph_a2_refinery", "promoted_subgraph", "a1_graph_projection", "rosetta_v2"]
- **outputs**: ["identity_registry_v1", "identity_bridge_contracts_v1", "identity_registry_build_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/identity-registry-builder/SKILL.md", "gemini": "system_v4/skill_specs/identity-registry-builder/SKILL.md", "shell": "system_v4/skills/identity_registry_builder.py"}
- **related_skills**: ["graph-capability-auditor", "nested-graph-layer-auditor", "ratchet-a2-a1"]

## Outward Relations
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **RELATED_TO** → [[ratchet-a2-a1]]
- **SKILL_OPERATES_ON** → [[KERNEL__IDENTITY_EMERGENCE]]

## Inward Relations
- [[a1-jargoned-graph-builder]] → **RELATED_TO**
- [[a1-jargoned-scope-aligner]] → **RELATED_TO**
- [[a2-high-intake-graph-builder]] → **RELATED_TO**
- [[a2-low-control-graph-builder]] → **RELATED_TO**
- [[a2-mid-refinement-graph-builder]] → **RELATED_TO**
- [[identity-registry-overlap-quarantine]] → **RELATED_TO**
