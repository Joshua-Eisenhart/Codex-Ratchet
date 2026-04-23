---
skill_id: a2-next-state-first-target-context-consumer-proof-operator
name: a2-next-state-first-target-context-consumer-proof-operator
description: Metadata-only proof slice that exercises the admitted first-target next-state context consumer seam without widening skill-improver write authority
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, consumer_report_path, consumer_packet_path, bridge_report_path, bridge_packet_path, target_selection_packet_path, first_target_proof_report_path, report_json_path, report_md_path, packet_path]
outputs: [next_state_first_target_context_consumer_proof_report, next_state_first_target_context_consumer_proof_packet]
related_skills: [skill-improver-operator, a2-next-state-improver-context-bridge-audit-operator, a2-next-state-first-target-context-consumer-admission-audit-operator, a2-skill-improver-first-target-proof-operator]
capabilities:
  can_write_repo: false
  reads_graph: true
tool_dependencies: []
provenance: "OpenClaw-RL-derived next-state bridge plus Ratchet-native skill-improver gate surfaces retooled into a bounded metadata-only first-target consumer proof"
adapters:
  codex: system_v4/skill_specs/a2-next-state-first-target-context-consumer-proof-operator/SKILL.md
  shell: system_v4/skills/a2_next_state_first_target_context_consumer_proof_operator.py
---

# A2 Next-State First-Target Context Consumer Proof Operator

Use this skill when the next-state bridge and consumer-admission audits are both
green and we need one bounded proof that `skill-improver-operator` can ingest
first-target context metadata without widening write authority.

## Purpose

- read the current next-state bridge and consumer-admission packets
- read the current selected and proven first target
- run `skill-improver-operator` in dry-run mode only
- pass metadata-only next-state context into the owner skill
- emit one repo-held proof report and one packet

## Execute Now

1. Read:
   - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json)
   - [A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json)
   - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json)
   - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json)
   - [SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json)
   - [SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json)
2. Only prove:
   - the currently selected and already proven first target
   - metadata-only context ingestion
   - dry-run/no-write behavior
3. Keep the result explicit about:
   - `metadata_only_context_loaded`
   - `write_permitted = false`
   - retained general gate

## Quality Gates

- Do not write to the target skill.
- Do not widen to second-target admission, graph backfill, runtime import, or live learning.
- Do not claim that this proof creates a general-purpose context consumer lane.
- Keep the next step fail-closed and audit-only.
