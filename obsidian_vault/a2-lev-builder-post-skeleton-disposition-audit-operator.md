---
id: "SKILL::a2-lev-builder-post-skeleton-disposition-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-builder-post-skeleton-disposition-audit-operator
**Node ID:** `SKILL::a2-lev-builder-post-skeleton-disposition-audit-operator`

## Description
Audit-only post-skeleton disposition operator that decides whether the selected lev-builder unresolved branch should stay open, hold, or retire without widening into runtime claims

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_builder_post_skeleton_disposition_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "selector_report_path", "selector_packet_path", "readiness_report_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["lev_builder_post_skeleton_disposition_audit_report", "lev_builder_post_skeleton_disposition_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-builder-post-skeleton-disposition-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_builder_post_skeleton_disposition_audit_operator.py", "dispatch_bi
- **related_skills**: ["a2-lev-builder-post-skeleton-follow-on-selector-operator", "a2-lev-builder-post-skeleton-readiness-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-builder-post-skeleton-follow-on-selector-operator]]
- **RELATED_TO** → [[a2-lev-builder-post-skeleton-readiness-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **MEMBER_OF** → [[Lev Formalization Placement]]

## Inward Relations
- [[a2-lev-builder-post-skeleton-future-lane-existence-audit-operator]] → **RELATED_TO**
