---
id: "SKILL::a2-lev-agents-promotion-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-agents-promotion-operator
**Node ID:** `SKILL::a2-lev-agents-promotion-operator`

## Description
Audit-only operator that ranks the next lev-os/agents cluster to promote into Ratchet-native form

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_agents_promotion_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["a2_lev_agents_promotion_report", "a2_lev_agents_promotion_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-agents-promotion-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_agents_promotion_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-skill-source-intake-operator", "a2-tracked-work-operator", "a2-workshop-analysis-gate-operator"]

## Outward Relations
- **RELATED_TO** → [[a2-skill-source-intake-operator]]
- **RELATED_TO** → [[a2-tracked-work-operator]]
- **RELATED_TO** → [[a2-workshop-analysis-gate-operator]]
- **SKILL_OPERATES_ON** → [[lev_os_skill_system]]
- **MEMBER_OF** → [[Lev Architecture Fitness Review]]

## Inward Relations
- [[a2-lev-builder-placement-audit-operator]] → **RELATED_TO**
- [[a2-lev-builder-formalization-proposal-operator]] → **RELATED_TO**
- [[a2-lev-autodev-loop-audit-operator]] → **RELATED_TO**
- [[a2-lev-architecture-fitness-operator]] → **RELATED_TO**
- [[a2-source-family-lane-selector-operator]] → **RELATED_TO**
