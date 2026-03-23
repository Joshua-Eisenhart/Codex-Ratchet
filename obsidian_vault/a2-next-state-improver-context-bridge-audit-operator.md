---
id: "SKILL::a2-next-state-improver-context-bridge-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-next-state-improver-context-bridge-audit-operator
**Node ID:** `SKILL::a2-next-state-improver-context-bridge-audit-operator`

## Description
Audit-only bridge that decides whether current next-state witness signals can populate a bounded skill-improver context surface without widening mutation authority

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_next_state_improver_context_bridge_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo", "probe_report_path", "probe_packet_path", "witness_path", "readiness_report_path", "first_target_proof_report_path", "second_target_packet_path", "report_path", "markdown_path", "packet_path"
- **outputs**: ["next_state_improver_context_bridge_audit_report", "next_state_improver_context_bridge_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-next-state-improver-context-bridge-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_next_state_improver_context_bridge_audit_operator.py", "dispatch_binding"
- **related_skills**: ["a2-next-state-directive-signal-probe-operator", "witness-recorder", "skill-improver-operator", "a2-skill-improver-readiness-operator", "a2-skill-improver-first-target-proof-operator", "a2-skill-impr

## Outward Relations
- **RELATED_TO** → [[a2-next-state-directive-signal-probe-operator]]
- **RELATED_TO** → [[witness-recorder]]
- **RELATED_TO** → [[skill-improver-operator]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **RELATED_TO** → [[a2-skill-improver-first-target-proof-operator]]
- **RELATED_TO** → [[a2-skill-improver-second-target-admission-audit-operator]]

## Inward Relations
- [[a2-next-state-first-target-context-consumer-admission-audit-operator]] → **RELATED_TO**
- [[a2-next-state-first-target-context-consumer-proof-operator]] → **RELATED_TO**
