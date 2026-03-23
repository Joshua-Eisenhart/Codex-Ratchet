---
id: "SKILL::a2-entropy-bridge-helper-decomposition-control"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-entropy-bridge-helper-decomposition-control
**Node ID:** `SKILL::a2-entropy-bridge-helper-decomposition-control`

## Description
Run one bounded A2-only helper-decomposition control pass for correlation_diversity_functional and write an explicit audit that confirms compound bridge heads stay proposal-side while colder witnesses remain the executable floor.

## Properties
- **skill_type**: correction
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/a2-entropy-bridge-helper-decomposition-control/SKILL.md
- **status**: active
- **applicable_layers**: []
- **applicable_trust_zones**: []
- **applicable_graphs**: ["concept"]
- **inputs**: ["a2_stage1_operatorized_entropy_head_refinement_audit", "helper_decomposition_control_surface", "executable_entrypoint_surface"]
- **outputs**: ["a2_entropy_bridge_helper_decomposition_control_audit"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-entropy-bridge-helper-decomposition-control/SKILL.md", "gemini": "system_v4/skill_specs/a2-entropy-bridge-helper-decomposition-control/SKILL.md", "shell": "system_v
- **related_skills**: ["a2-stage1-operatorized-entropy-head-refinement", "graph-capability-auditor", "nested-graph-layer-auditor"]

## Outward Relations
- **RELATED_TO** → [[a2-stage1-operatorized-entropy-head-refinement]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[nested-graph-layer-auditor]]
- **SKILL_OPERATES_ON** → [[a2_entropy_reduction_mission]]

## Inward Relations
- [[a2-colder-witness-execution-consolidation]] → **RELATED_TO**
