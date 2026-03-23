---
id: "SKILL::outer-session-ledger"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# outer-session-ledger
**Node ID:** `SKILL::outer-session-ledger`

## Description
Outer session ledger continuity operator

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/outer_session_ledger.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["runtime", "control", "a2_low_control_graph_v1"]
- **inputs**: ["repo", "sessions_root", "host_kind", "state_path", "events_path", "report_json_path", "report_md_path"]
- **outputs**: ["outer_session_ledger_state", "outer_session_ledger_report"]
- **adapters**: {"shell": "system_v4/skills/outer_session_ledger.py", "dispatch_binding": "python_module"}
- **related_skills**: ["a2-brain-surface-refresher", "a2-workshop-analysis-gate-operator", "witness-evermem-sync"]

## Outward Relations
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **RELATED_TO** → [[a2-workshop-analysis-gate-operator]]
- **RELATED_TO** → [[witness-evermem-sync]]
- **SKILL_OPERATES_ON** → [[a2_controller_dispatch_first]]

## Inward Relations
- [[outside-control-shell-operator]] → **RELATED_TO**
