---
skill_id: a2-next-state-first-target-context-consumer-admission-audit-operator
name: a2-next-state-first-target-context-consumer-admission-audit-operator
description: Audit-only slice that decides whether the landed next-state bridge has any explicit first-target consumer contract in the current skill-improver lane.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo, bridge_report_path, bridge_packet_path, target_selection_packet_path, first_target_proof_report_path, second_target_packet_path, report_path, markdown_path, packet_path]
outputs: [next_state_first_target_context_consumer_admission_report, next_state_first_target_context_consumer_admission_packet]
related_skills: [a2-next-state-improver-context-bridge-audit-operator, skill-improver-operator, a2-skill-improver-target-selector-operator, a2-skill-improver-first-target-proof-operator, a2-skill-improver-second-target-admission-audit-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "OpenClaw-RL-derived next-state bridge plus Ratchet-native skill-improver gate surfaces retooled into a bounded first-target consumer-admission audit"
adapters:
  codex: system_v4/skill_specs/a2-next-state-first-target-context-consumer-admission-audit-operator/SKILL.md
  shell: system_v4/skills/a2_next_state_first_target_context_consumer_admission_audit_operator.py
---

# A2 Next-State First-Target Context Consumer Admission Audit Operator

Use this skill after the next-state improver/context bridge is landed when we
need one honest answer to the next question: does the current one-proven-target
skill-improver lane have any explicit first-target consumer contract for that
bridge, or do we still only have a bridge packet with nowhere honest to land?

## Purpose

- read the current bridge packet and bridge report
- read the current first-target proof / target selection / second-target hold surfaces
- inspect the current `skill-improver-operator` input contract for an explicit context seam
- emit one repo-held report and packet that either admits a bounded consumer audit path or fails closed

## Execute Now

1. Read:
   - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json)
   - [A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json)
   - [SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json)
   - [SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json)
   - [SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json)
   - [skill-improver-operator spec](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skill_specs/skill-improver-operator/SKILL.md)
   - [skill_improver_operator.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skills/skill_improver_operator.py)
2. Only admit a consumer path if:
   - the bridge packet is `ok`
   - the bridge is first-target-context-only
   - the current first proven target matches the current selected target
   - the general second-target gate is still held
   - there is an explicit context-ingest contract in the current consumer surface
3. Emit one repo-held report and packet with the bounded verdict.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_FIRST_TARGET_CONTEXT_CONSUMER_ADMISSION_AUDIT_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not mutate any target skill or witness surface from this slice.
- Do not invent a context seam if the current operator contract does not expose one.
- Do not widen this into second-target admission, live learning, runtime import, or graph backfill.
- Keep the result audit-only and fail closed if the consumer contract is absent.
