---
id: "SKILL::a2-lev-builder-post-skeleton-follow-on-selector-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-builder-post-skeleton-follow-on-selector-operator
**Node ID:** `SKILL::a2-lev-builder-post-skeleton-follow-on-selector-operator`

## Description
Selector-only post-skeleton follow-on operator that chooses the smallest honest lev-builder unresolved branch without widening into migration or runtime claims

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_builder_post_skeleton_follow_on_selector_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "readiness_report_path", "readiness_packet_path", "skeleton_report_path", "skeleton_packet_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["lev_builder_post_skeleton_follow_on_selector_report", "lev_builder_post_skeleton_follow_on_selector_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-builder-post-skeleton-follow-on-selector-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_builder_post_skeleton_follow_on_selector_operator.py", "dispatch_
- **related_skills**: ["a2-lev-builder-post-skeleton-readiness-operator", "a2-lev-builder-formalization-skeleton-operator", "a2-lev-builder-placement-audit-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-builder-post-skeleton-readiness-operator]]
- **RELATED_TO** → [[a2-lev-builder-formalization-skeleton-operator]]
- **RELATED_TO** → [[a2-lev-builder-placement-audit-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **MEMBER_OF** → [[Lev Formalization Placement]]

## Inward Relations
- [[a2-lev-builder-post-skeleton-disposition-audit-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-future-lane-existence-audit-operator]] → **RELATED_TO**
