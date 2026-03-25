---
skill_id: a2-skill-improver-second-target-admission-audit-operator
name: a2-skill-improver-second-target-admission-audit-operator
description: Audit-only follow-on that decides whether skill-improver-operator should hold at one proven target or admit one second bounded native target class.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, report_json_path, report_md_path, packet_path]
outputs: [skill_improver_second_target_admission_report, skill_improver_second_target_admission_packet]
related_skills: [skill-improver-operator, a2-skill-improver-readiness-operator, a2-skill-improver-target-selector-operator, a2-skill-improver-first-target-proof-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native follow-on audit that turns one proven first target into an explicit hold-vs-second-target-class decision"
adapters:
  codex: system_v4/skill_specs/a2-skill-improver-second-target-admission-audit-operator/SKILL.md
  shell: system_v4/skills/a2_skill_improver_second_target_admission_audit_operator.py
---

# A2 Skill Improver Second Target Admission Audit Operator

Use this skill after the first bounded `skill-improver-operator` proof when we
need one honest answer to the next question: do we hold at one proven target,
or has a second bounded native target class earned admission?

## Purpose

- read the current readiness, target-selection, and first-target proof surfaces
- inspect the live native maintenance skill set for a stricter second-target class
- fail closed if the remaining candidates are too central, too self-referential, or too externally coupled
- emit one repo-held report and packet

## Execute Now

1. Read:
   - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
   - [SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json)
   - [SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1.json)
2. Only consider second-target candidates from the bounded native maintenance class:
   - active Python operator skill
   - dedicated codex spec exists
   - dedicated smoke exists
   - propose-only / audit-style behavior
   - not imported-cluster
3. Fail closed on:
   - already-proven first target
   - controller-critical truth-maintenance surfaces
   - self-referential skill-improver lane members
   - side-project / external-dependency targets
4. Emit:
   - current report
   - compact packet

## Default Outputs

When no explicit paths are supplied, write:

- `system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/SKILL_IMPROVER_SECOND_TARGET_ADMISSION_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not mutate any target skill from this slice.
- Do not widen to general live repo mutation.
- Do not admit imported-cluster or side-project targets as the second target class.
- Keep the output honest even if the only correct answer is `hold_one_proven_target_only`.
