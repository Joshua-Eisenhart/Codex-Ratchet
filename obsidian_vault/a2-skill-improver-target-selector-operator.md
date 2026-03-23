---
id: "SKILL::a2-skill-improver-target-selector-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-skill-improver-target-selector-operator
**Node ID:** `SKILL::a2-skill-improver-target-selector-operator`

## Description
Audit-only selector for the first bounded target class for skill-improver-operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_skill_improver_target_selector_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["skill_improver_target_selection_report", "skill_improver_target_selection_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-skill-improver-target-selector-operator/SKILL.md", "shell": "system_v4/skills/a2_skill_improver_target_selector_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["skill-improver-operator", "a2-skill-improver-readiness-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[a2-skill-improver-dry-run-operator]] → **RELATED_TO**
- [[a2-skill-improver-first-target-proof-operator]] → **RELATED_TO**
- [[a2-skill-improver-second-target-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-first-target-context-consumer-admission-audit-operator]] → **RELATED_TO**
