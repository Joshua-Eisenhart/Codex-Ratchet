---
id: "SKILL::a2-next-state-directive-signal-probe-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-next-state-directive-signal-probe-operator
**Node ID:** `SKILL::a2-next-state-directive-signal-probe-operator`

## Description
Probe the live witness corpus for bounded next-state and directive-correction evidence without claiming live learning or mutation

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_next_state_directive_signal_probe_operator.py
- **status**: active
- **applicable_layers**: ["A2_MID_REFINEMENT", "B_ADJUDICATED"]
- **applicable_trust_zones**: ["A2_MID_REFINEMENT", "B_ADJUDICATED"]
- **applicable_graphs**: ["runtime", "control", "a2_mid_refinement_graph_v1"]
- **inputs**: ["repo", "next_state_audit_path", "witness_path", "readiness_report_path", "report_path", "markdown_path", "packet_path"]
- **outputs**: ["next_state_directive_signal_probe_report", "next_state_directive_signal_probe_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-next-state-directive-signal-probe-operator/SKILL.md", "shell": "system_v4/skills/a2_next_state_directive_signal_probe_operator.py", "dispatch_binding": "python_modu
- **related_skills**: ["a2-next-state-signal-adaptation-audit-operator", "witness-recorder", "runtime-state-kernel", "a2-skill-improver-readiness-operator"]

## Outward Relations
- **RELATED_TO** → [[a2-next-state-signal-adaptation-audit-operator]]
- **RELATED_TO** → [[witness-recorder]]
- **RELATED_TO** → [[runtime-state-kernel]]
- **RELATED_TO** → [[a2-skill-improver-readiness-operator]]
- **SKILL_OPERATES_ON** → [[karpathy_autoresearch_cegis_loop]]

## Inward Relations
- [[a2-next-state-improver-context-bridge-audit-operator]] → **RELATED_TO**
