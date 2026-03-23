---
id: "SKILL::a2-skill-improver-first-target-proof-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-skill-improver-first-target-proof-operator
**Node ID:** `SKILL::a2-skill-improver-first-target-proof-operator`

## Description
Bounded first-target proof slice for skill-improver-operator using the selected target only

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_skill_improver_first_target_proof_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "proof_mode", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["skill_improver_first_target_proof_report", "skill_improver_first_target_proof_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-skill-improver-first-target-proof-operator/SKILL.md", "shell": "system_v4/skills/a2_skill_improver_first_target_proof_operator.py", "dispatch_binding": "python_modu
- **related_skills**: ["skill-improver-operator", "a2-skill-improver-readiness-operator", "a2-skill-improver-target-selector-operator", "a2-skill-improver-dry-run-operator"]

## Outward Relations
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **RELATED_TO** → [[a2-skill-improver-target-selector-operator]]
- **RELATED_TO** → [[a2-skill-improver-dry-run-operator]]
- **MEMBER_OF** → [[A2 Skill Truth Maintenance]]

## Inward Relations
- [[a2-next-state-signal-adaptation-audit-operator]] → **RELATED_TO**
- [[a2-skill-improver-second-target-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-improver-context-bridge-audit-operator]] → **RELATED_TO**
- [[a2-next-state-first-target-context-consumer-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-first-target-context-consumer-proof-operator]] → **RELATED_TO**
