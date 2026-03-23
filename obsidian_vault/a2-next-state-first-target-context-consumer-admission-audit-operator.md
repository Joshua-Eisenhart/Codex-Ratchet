---
id: "SKILL::a2-next-state-first-target-context-consumer-admission-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-next-state-first-target-context-consumer-admission-audit-operator
**Node ID:** `SKILL::a2-next-state-first-target-context-consumer-admission-audit-operator`

## Description
Audit-only slice that decides whether the landed next-state bridge has any explicit first-target consumer contract in the current skill-improver lane

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_next_state_first_target_context_consumer_admission_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo", "bridge_report_path", "bridge_packet_path", "target_selection_packet_path", "first_target_proof_report_path", "second_target_packet_path", "report_path", "markdown_path", "packet_path"]
- **outputs**: ["next_state_first_target_context_consumer_admission_report", "next_state_first_target_context_consumer_admission_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-next-state-first-target-context-consumer-admission-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_next_state_first_target_context_consumer_admission_audit_
- **related_skills**: ["a2-next-state-improver-context-bridge-audit-operator", "skill-improver-operator", "a2-skill-improver-target-selector-operator", "a2-skill-improver-first-target-proof-operator", "a2-skill-improver-se

## Outward Relations
- **RELATED_TO** → [[a2-next-state-improver-context-bridge-audit-operator]]
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-skill-improver-target-selector-operator]]
- **RELATED_TO** → [[a2-skill-improver-first-target-proof-operator]]
- **RELATED_TO** → [[a2-skill-improver-second-target-admission-audit-operator]]

## Inward Relations
- [[a2-next-state-first-target-context-consumer-proof-operator]] → **RELATED_TO**
