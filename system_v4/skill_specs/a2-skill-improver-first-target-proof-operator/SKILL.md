---
skill_id: a2-skill-improver-first-target-proof-operator
name: a2-skill-improver-first-target-proof-operator
description: Bounded first-target proof slice for skill-improver-operator using the currently selected target
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, proof_mode, report_json_path, report_md_path, packet_path]
outputs: [skill_improver_first_target_proof_report, skill_improver_first_target_proof_packet]
related_skills: [skill-improver-operator, a2-skill-improver-readiness-operator, a2-skill-improver-target-selector-operator]
capabilities:
  can_write_repo: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native bounded proof slice that demonstrates one selected skill-improver target under explicit allowlist + approval-token control"
adapters:
  codex: system_v4/skill_specs/a2-skill-improver-first-target-proof-operator/SKILL.md
  shell: system_v4/skills/a2_skill_improver_first_target_proof_operator.py
---

# A2 Skill Improver First Target Proof Operator

Use this skill when `skill-improver-operator` already has a selected first
target and we need one bounded proof that the gated write path can succeed
without widening to general live mutation.

## Purpose

- read the current selected first target
- run one bounded proof against that target only
- restore the exact original target file bytes
- emit one repo-held proof report and one packet

## Execute Now

1. Read:
   - [SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_REPORT__CURRENT__v1.json)
   - [SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_TARGET_SELECTION_PACKET__CURRENT__v1.json)
   - [skill-improver-operator spec](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skill_specs/skill-improver-operator/SKILL.md)
2. Only prove:
   - the currently selected first target
   - a harmless reversible mutation
   - explicit allowlist + approval-token control
3. Restore the exact original target bytes before exit.

## Quality Gates

- Do not widen this into general live repo mutation.
- Do not leave the target file changed after the proof finishes.
- Do not skip the real target smoke after the gated commit.
- Keep the result explicit about “one proven target” versus “general mutator.”
