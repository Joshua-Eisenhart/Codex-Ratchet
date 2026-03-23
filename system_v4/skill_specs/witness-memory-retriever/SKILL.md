---
skill_id: witness-memory-retriever
name: witness-memory-retriever
description: Bounded EverMem witness-memory retrieval probe that attempts one witness-derived lookup and emits repo-held report surfaces without claiming bootstrap or broader memory integration.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, B_ADJUDICATED]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs:
  - repo_root
  - witness_path
  - sync_report_path
  - query
  - evermem_url
  - timeout_seconds
  - report_json_path
  - report_md_path
  - packet_path
outputs:
  - witness_memory_retriever_report
  - witness_memory_retriever_packet
related_skills:
  - witness-evermem-sync
  - evermem-memory-backend-adapter
  - outside-control-shell-operator
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native bounded retrieval probe over the EverMem witness seam"
adapters:
  codex: system_v4/skill_specs/witness-memory-retriever/SKILL.md
  shell: system_v4/skills/witness_memory_retriever.py
---

# Witness Memory Retriever

Use this skill when we need one bounded retrieval probe over the existing
EverMem witness seam without widening into startup bootstrap or broader memory
claims.

## Purpose

- stay on the already-proven witness seam
- derive one bounded retrieval query from an explicit query or the latest witness
- emit one repo-held report and one packet
- keep the result audit-only, observer-only, and non-bootstrap

## Execute Now

1. Read:
   - [EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json)
   - [witness_corpus_v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/witness_corpus_v1.json)
   - [evermem_adapter.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skills/evermem_adapter.py)
2. Attempt one bounded retrieval probe only.
3. Keep the slice report-only and non-bootstrap.

## Default Outputs

- `system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not claim startup boot restore or A2 bootstrap.
- Do not claim pi-mono integration or outside-control-shell integration.
- Do not claim durable memory law or general context recovery.
- Do not claim semantic quality guarantees beyond attempted bounded retrieval.
- Do not mutate canonical A2 state, witness state, or EverMem sync state from this slice.
