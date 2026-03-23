---
id: "SKILL::a2-evermem-backend-reachability-audit-operator"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# a2-evermem-backend-reachability-audit-operator
**Node ID:** `SKILL::a2-evermem-backend-reachability-audit-operator`

## Description
Bounded EverMem backend reachability audit over local bring-up prerequisites, Docker daemon, and localhost probes

## Properties
- **skill_type**: maintenance
- **source_type**: operator_module
- **source_path**: system_v4/skills/a2_evermem_backend_reachability_audit_operator.py
- **status**: active
- **applicable_layers**: ["A2_LOW_CONTROL", "A2_MID_REFINEMENT"]
- **applicable_trust_zones**: ["A2_LOW_CONTROL", "A2_MID_REFINEMENT"]
- **applicable_graphs**: ["runtime", "control", "a2_low_control_graph_v1"]
- **inputs**: ["repo_root", "evermemos_repo_path", "health_url", "retrieval_report_path", "sync_report_path", "timeout_seconds", "report_json_path", "report_md_path", "packet_path"]
- **outputs**: ["evermem_backend_reachability_audit_report", "evermem_backend_reachability_audit_packet"]
- **adapters**: {"codex": "system_v4/skill_specs/a2-evermem-backend-reachability-audit-operator/SKILL.md", "dispatch_binding": "python_module", "shell": "system_v4/skills/a2_evermem_backend_reachability_audit_operato
- **related_skills**: ["witness-memory-retriever", "witness-evermem-sync", "a2-brain-surface-refresher", "outside-control-shell-operator"]

## Outward Relations
- **RELATED_TO** → [[witness-memory-retriever]]
- **RELATED_TO** → [[witness-evermem-sync]]
- **RELATED_TO** → [[a2-brain-surface-refresher]]
- **RELATED_TO** → [[outside-control-shell-operator]]
