---
id: "SKILL::a2-next-state-first-target-context-consumer-proof-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-next-state-first-target-context-consumer-proof-operator
**Node ID:** `SKILL::a2-next-state-first-target-context-consumer-proof-operator`

## Description
Metadata-only proof slice that exercises the admitted first-target next-state context consumer seam without widening skill-improver write authority

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_next_state_first_target_context_consumer_proof_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo_root", "consumer_report_path", "consumer_packet_path", "bridge_report_path", "bridge_packet_path", "target_selection_packet_path", "first_target_proof_report_path", "report_json_path", "report_
- **outputs**: ["next_state_first_target_context_consumer_proof_report", "next_state_first_target_context_consumer_proof_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-next-state-first-target-context-consumer-proof-operator/SKILL.md", "shell": "system_v4/skills/a2_next_state_first_target_context_consumer_proof_operator.py", "dispa
- **related_skills**: ["skill-improver-operator", "a2-next-state-improver-context-bridge-audit-operator", "a2-next-state-first-target-context-consumer-admission-audit-operator", "a2-skill-improver-first-target-proof-operat

## Outward Relations
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-next-state-improver-context-bridge-audit-operator]]
- **RELATED_TO** → [[a2-next-state-first-target-context-consumer-admission-audit-operator]]
- **RELATED_TO** → [[a2-skill-improver-first-target-proof-operator]]
