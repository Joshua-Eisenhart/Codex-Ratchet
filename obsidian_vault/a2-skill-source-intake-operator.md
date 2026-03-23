---
id: "SKILL::a2-skill-source-intake-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-skill-source-intake-operator
**Node ID:** `SKILL::a2-skill-source-intake-operator`

## Description
A2-side skill source intake audit operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_skill_source_intake_operator.py
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["runtime", "control", "a2_high_intake_graph_v1"]
- **inputs**: ["repo_root", "report_path"]
- **outputs**: ["intake_report"]
- **adapters**: {"shell": "system_v4/skills/a2_skill_source_intake_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["skill-improver-operator", "autoresearch-operator", "witness-evermem-sync"]

## Outward Relations
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[autoresearch-operator]]
- **RELATED_TO** → [[witness-evermem-sync]]
- **SKILL_OPERATES_ON** → [[a2_entropy_reduction_mission]]

## Inward Relations
- [[a2-tracked-work-operator]] → **RELATED_TO**
- [[a2-workshop-analysis-gate-operator]] → **RELATED_TO**
- [[a2-lev-agents-promotion-operator]] → **RELATED_TO**
- [[a2-source-family-lane-selector-operator]] → **RELATED_TO**
- [[a2-context-spec-workflow-pattern-audit-operator]] → **RELATED_TO**
