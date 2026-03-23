---
id: "SKILL::a2-lev-architecture-fitness-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-lev-architecture-fitness-operator
**Node ID:** `SKILL::a2-lev-architecture-fitness-operator`

## Description
Audit-only operator that audits one bounded lev architecture and fitness guidance slice before any broader review, migration, or runtime claim

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_lev_architecture_fitness_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "candidate", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["lev_architecture_fitness_report", "lev_architecture_fitness_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-lev-architecture-fitness-operator/SKILL.md", "shell": "system_v4/skills/a2_lev_architecture_fitness_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-lev-agents-promotion-operator", "a2-lev-autodev-loop-audit-operator", "a2-brain-surface-refresher"]

## Outward Relations
- **RELATED_TO** → [[a2-lev-agents-promotion-operator]]
- **RELATED_TO** → [[a2-lev-autodev-loop-audit-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **SKILL_OPERATES_ON** → [[lev_os_skill_system]]
- **MEMBER_OF** → [[Lev Architecture Fitness Review]]
