---
id: "SKILL::a2-skill-improver-readiness-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-skill-improver-readiness-operator
**Node ID:** `SKILL::a2-skill-improver-readiness-operator`

## Description
Audit-only readiness operator for skill-improver-operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_skill_improver_readiness_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "target_skill_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["skill_improver_readiness_report", "skill_improver_readiness_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md", "shell": "system_v4/skills/a2_skill_improver_readiness_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["skill-improver-operator", "a2-brain-surface-refresher", "graph-capability-auditor"]

## Outward Relations
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **RELATED_TO** → [[graph-capability-auditor]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[skill-improver-operator]] → **RELATED_TO**
- [[a2-skill-improver-target-selector-operator]] → **RELATED_TO**
- [[a2-skill-improver-dry-run-operator]] → **RELATED_TO**
- [[a2-skill-improver-first-target-proof-operator]] → **RELATED_TO**
- [[a2-next-state-signal-adaptation-audit-operator]] → **RELATED_TO**
- [[a2-next-state-directive-signal-probe-operator]] → **RELATED_TO**
- [[a2-skill-improver-second-target-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-improver-context-bridge-audit-operator]] → **RELATED_TO**
