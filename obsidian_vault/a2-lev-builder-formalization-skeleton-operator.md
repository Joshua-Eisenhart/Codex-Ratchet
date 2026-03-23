---
id: "SKILL::a2-lev-builder-formalization-skeleton-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-builder-formalization-skeleton-operator
**Node ID:** `SKILL::a2-lev-builder-formalization-skeleton-operator`

## Description
Scaffold-only operator that proves the bounded lev-builder formalization scaffold bundle is landed without widening into migration or runtime claims

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "proposal_report_path", "proposal_packet_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["lev_builder_formalization_skeleton_report", "lev_builder_formalization_skeleton_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-builder-formalization-skeleton-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_builder_formalization_skeleton_operator.py", "dispatch_binding": "python_mo
- **related_skills**: ["a2-lev-builder-formalization-proposal-operator", "a2-lev-builder-placement-audit-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-builder-formalization-proposal-operator]]
- **RELATED_TO** → [[a2-lev-builder-placement-audit-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **SKILL_OPERATES_ON** → [[lev_os_skill_system]]
- **MEMBER_OF** → [[Lev Formalization Placement]]

## Inward Relations
- [[a2-lev-builder-post-skeleton-readiness-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-follow-on-selector-operator]] → **RELATED_TO**
