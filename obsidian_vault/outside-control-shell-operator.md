---
id: "SKILL::outside-control-shell-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# outside-control-shell-operator
**Node ID:** `SKILL::outside-control-shell-operator`

## Description
Read-only pi-mono outside session host audit operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/outside_control_shell_operator.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["runtime", "control", "a2_low_control_graph_v1"]
- **inputs**: ["repo", "target_surface_path", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["outside_session_host_report", "outside_session_host_packet"]
- **adapters**: {"shell": "system_v4/skills/outside_control_shell_operator.py", "dispatch_binding": "python_module"}
- **related_skills**: ["outer-session-ledger", "a2-brain-surface-refresher", "a2-workshop-analysis-gate-operator"]

## Outward Relations
- **RELATED_TO** → [[outer-session-ledger]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **RELATED_TO** → [[a2-workshop-analysis-gate-operator]]
- **SKILL_OPERATES_ON** → [[a2_controller_dispatch_first]]

## Inward Relations
- [[witness-memory-retriever]] → **RELATED_TO**
- [[a2-evermem-backend-reachability-audit-operator]] → **RELATED_TO**
