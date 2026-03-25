---
skill_id: a2-next-state-improver-context-bridge-audit-operator
name: a2-next-state-improver-context-bridge-audit-operator
description: Audit-only bridge that decides whether current next-state witness signals can populate a bounded skill-improver context surface without widening mutation authority.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo, probe_report_path, probe_packet_path, witness_path, readiness_report_path, first_target_proof_report_path, second_target_packet_path, report_path, markdown_path, packet_path]
outputs: [next_state_improver_context_bridge_audit_report, next_state_improver_context_bridge_audit_packet]
related_skills: [a2-next-state-directive-signal-probe-operator, witness-recorder, skill-improver-operator, a2-skill-improver-readiness-operator, a2-skill-improver-first-target-proof-operator, a2-skill-improver-second-target-admission-audit-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "OpenClaw-RL-derived next-state signal lane plus Ratchet-native skill-improver truth maintenance retooled into a bounded context-bridge audit slice"
adapters:
  codex: system_v4/skill_specs/a2-next-state-improver-context-bridge-audit-operator/SKILL.md
  shell: system_v4/skills/a2_next_state_improver_context_bridge_audit_operator.py
---

# A2 Next-State Improver Context Bridge Audit Operator

Use this skill after the next-state directive probe turns green when we need one
honest answer to the next question: do the current witness-derived directive
signals earn a bounded context bridge into the existing skill-improver lane, or
do we still only have isolated witness traces?

## Purpose

- read the current next-state probe outputs and the live witness corpus
- read the current skill-improver readiness / first-target-proof / second-target-hold surfaces
- decide whether there is enough repo-held evidence for a context-only bridge
- keep the result fenced to the one proven target class and audit-only use

## Execute Now

1. Read:
   - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_REPORT__CURRENT__v1.json)
   - [A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_DIRECTIVE_SIGNAL_PROBE_PACKET__CURRENT__v1.json)
   - [system_v4/a2_state/witness_corpus_v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/witness_corpus_v1.json)
   - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
   - [SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json)
   - [SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json)
2. Only bridge:
   - real post-action witness entries
   - directive-bearing next-state evidence
   - one proven target class only
3. Emit one repo-held report and packet with the bounded verdict.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_NEXT_STATE_IMPROVER_CONTEXT_BRIDGE_AUDIT_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not mutate the witness corpus or skill-improver targets.
- Do not treat this as second-target admission.
- Do not widen this into live learning, online training, or OpenClaw runtime claims.
- Do not seed graph links or graph backfill claims from this slice.
- Keep the result audit-only, nonoperative, and limited to first-target context use.
