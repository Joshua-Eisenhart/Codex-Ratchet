---
id: "SKILL::a2-next-state-signal-adaptation-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-next-state-signal-adaptation-audit-operator
**Node ID:** `SKILL::a2-next-state-signal-adaptation-audit-operator`

## Description
Bounded next-state signal adaptation audit operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_next_state_signal_adaptation_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "B_ADJUDICATED"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "B_ADJUDICATED"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo", "report_path", "markdown_path", "packet_path"]
- **outputs**: ["next_state_signal_adaptation_audit_report", "next_state_signal_adaptation_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-next-state-signal-adaptation-audit-operator/SKILL.md", "shell": "system_v4/skills/a2_next_state_signal_adaptation_audit_operator.py", "dispatch_binding": "python_mo
- **related_skills**: ["witness-recorder", "runtime-state-kernel", "bounded-improve-operator", "a2-skill-improver-readiness-operator", "a2-skill-improver-first-target-proof-operator"]

## Outward Relations
- **RELATED_TO** → [[witness-recorder]]
- **RELATED_TO** → [[runtime-state-kernel]]
- **RELATED_TO** → [[bounded-improve-operator]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **RELATED_TO** → [[a2-skill-improver-first-target-proof-operator]]
- **SKILL_OPERATES_ON** → [[karpathy_autoresearch_cegis_loop]]

## Inward Relations
- [[a2-next-state-directive-signal-probe-operator]] → **RELATED_TO**
