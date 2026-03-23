---
id: "SKILL::a2-lev-builder-formalization-proposal-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-builder-formalization-proposal-operator
**Node ID:** `SKILL::a2-lev-builder-formalization-proposal-operator`

## Description
Proposal-only operator that emits one bounded Ratchet-native formalization proposal after the lev-builder placement audit has landed

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_builder_formalization_proposal_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "placement_report_path", "placement_packet_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["lev_builder_formalization_proposal_report", "lev_builder_formalization_proposal_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-builder-formalization-proposal-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_builder_formalization_proposal_operator.py", "dispatch_binding": "python_mo
- **related_skills**: ["a2-lev-builder-placement-audit-operator", "a2-lev-agents-promotion-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-builder-placement-audit-operator]]
- **RELATED_TO** → [[a2-lev-agents-promotion-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **SKILL_OPERATES_ON** → [[lev_os_skill_system]]
- **MEMBER_OF** → [[Lev Formalization Placement]]

## Inward Relations
- [[a2-lev-builder-formalization-skeleton-operator]] → **RELATED_TO**
- [[a2-lev-builder-post-skeleton-readiness-operator]] → **RELATED_TO**
