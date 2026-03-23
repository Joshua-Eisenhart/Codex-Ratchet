---
id: "SKILL::a2-tracked-work-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-tracked-work-operator
**Node ID:** `SKILL::a2-tracked-work-operator`

## Description
A2 tracked work state operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_tracked_work_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "report_path"]
- **outputs**: ["work_state_report"]
- **adapters**: {"shell": "system_v4/skills/a2_tracked_work_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-skill-source-intake-operator", "skill-improver-operator"]

## Outward Relations
- **RELATED_TO** → [[a2-skill-source-intake-operator]]
- **RELATED_TO** → [[skill-improver-operator]]
- **MEMBER_OF** → [[Tracked Work Planning]]

## Inward Relations
- [[a2-research-deliberation-operator]] → **RELATED_TO**
- [[a2-brain-surface-refresher]] → **RELATED_TO**
- [[a2-workshop-analysis-gate-operator]] → **RELATED_TO**
- [[a2-lev-agents-promotion-operator]] → **RELATED_TO**
- [[a2-lev-autodev-loop-audit-operator]] → **RELATED_TO**
