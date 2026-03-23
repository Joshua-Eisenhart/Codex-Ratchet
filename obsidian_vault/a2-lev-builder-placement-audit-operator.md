---
id: "SKILL::a2-lev-builder-placement-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-builder-placement-audit-operator
**Node ID:** `SKILL::a2-lev-builder-placement-audit-operator`

## Description
Audit-only operator that audits one bounded lev-builder placement/formalization slice before any broader imported Lev promotion claim

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_builder_placement_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "candidate", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_lev_builder_placement_audit_report", "a2_lev_builder_placement_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-builder-placement-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_builder_placement_audit_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-lev-agents-promotion-operator", "a2-workshop-analysis-gate-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-agents-promotion-operator]]
- **RELATED_TO** → [[a2-workshop-analysis-gate-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **SKILL_OPERATES_ON** → [[lev_os_skill_system]]
- **MEMBER_OF** → [[Lev Formalization Placement]]

## Inward Relations
- [[a2-lev-builder-formalization-proposal-operator]] → **RELATED_TO**
- [[a2-lev-builder-formalization-skeleton-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-readiness-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-follow-on-selector-operator]] → **RELATED_TO**
