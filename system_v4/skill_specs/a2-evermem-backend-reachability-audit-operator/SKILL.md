---
skill_id: a2-evermem-backend-reachability-audit-operator
name: a2-evermem-backend-reachability-audit-operator
description: Emit one bounded repo-held audit of the local EverMemOS backend bring-up path, distinguishing tooling, Docker daemon, local repo prerequisites, and localhost reachability without starting services or claiming broader memory integration.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_MID_REFINEMENT]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs:
  - repo_root
  - evermemos_repo_path
  - health_url
  - retrieval_report_path
  - sync_report_path
  - timeout_seconds
  - report_json_path
  - report_md_path
  - packet_path
outputs:
  - evermem_backend_reachability_audit_report
  - evermem_backend_reachability_audit_packet
related_skills:
  - witness-memory-retriever
  - witness-evermem-sync
  - a2-brain-surface-refresher
  - outside-control-shell-operator
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native bounded audit over the local EverMemOS backend bring-up path and localhost reachability"
adapters:
  codex: system_v4/skill_specs/a2-evermem-backend-reachability-audit-operator/SKILL.md
  shell: system_v4/skills/a2_evermem_backend_reachability_audit_operator.py
---

# A2 EverMem Backend Reachability Audit Operator

Use this skill when the bounded EverMem retrieval slice is blocked and we need
one repo-held verdict about whether the local backend path is absent, unbooted,
unreachable, or mismatched.

## Purpose

- inspect the local EverMemOS repo bring-up prerequisites
- check Docker daemon reachability without starting services
- compare localhost health from `curl` and Python
- emit one repo-held report and packet
- keep the result audit-only and non-bootstrap

## Execute Now

1. Read:
   - [WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json)
   - [EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json)
   - [evermem_adapter.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skills/evermem_adapter.py)
   - [work/reference_repos/EverMind-AI/EverMemOS/README.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/work/reference_repos/EverMind-AI/EverMemOS/README.md)
2. Emit one bounded reachability audit only.
3. Do not start services or widen memory claims from this slice.

## Default Outputs

- `system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not start Docker services from this slice.
- Do not write `.env` or install dependencies from this slice.
- Do not claim startup bootstrap, pi-mono memory, or A2 replacement.
- Do not mutate canonical A2 state or EverMem runtime state from this slice.
