---
id: "SKILL::a2-lev-autodev-loop-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-autodev-loop-audit-operator
**Node ID:** `SKILL::a2-lev-autodev-loop-audit-operator`

## Description
Audit-only operator that audits one bounded lev autodev execution/validation loop slice before any broader recurring runtime claim

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_autodev_loop_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "candidate", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["lev_autodev_loop_audit_report", "lev_autodev_loop_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-autodev-loop-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_autodev_loop_audit_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-lev-agents-promotion-operator", "a2-tracked-work-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-agents-promotion-operator]]
- **RELATED_TO** → [[a2-tracked-work-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **SKILL_OPERATES_ON** → [[lev_os_skill_system]]
- **MEMBER_OF** → [[Lev Autodev Exec Validation]]

## Inward Relations
- [[a2-lev-architecture-fitness-operator]] → **RELATED_TO**
