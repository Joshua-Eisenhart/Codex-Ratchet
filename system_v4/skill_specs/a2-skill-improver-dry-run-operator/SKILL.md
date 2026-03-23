---
skill_id: a2-skill-improver-dry-run-operator
name: a2-skill-improver-dry-run-operator
description: Run one explicit first-target dry-run through skill-improver-operator and emit repo-held report surfaces without permitting repo mutation.
skill_type: operator
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [target_skill_id, candidate_code, report_json_path, report_md_path, packet_path]
outputs: [status, selected_target, improver_result, report_json_path, report_md_path, packet_path]
related_skills: [skill-improver-operator, a2-skill-improver-readiness-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  requires_human_gate: false
tool_dependencies: []
provenance: "Ratchet-native bounded first-target dry-run bridge over skill-improver-operator"
adapters:
  codex: system_v4/skill_specs/a2-skill-improver-dry-run-operator/SKILL.md
  shell: system_v4/skills/a2_skill_improver_dry_run_operator.py
---

# A2 Skill Improver Dry-Run Operator

Use this skill when `skill-improver-operator` needs to be exercised against one
explicit first target without granting any repo mutation power.

## Purpose

- keep the native maintenance cluster moving past readiness-only audit
- constrain the first live use to one allowlisted target
- keep the slice dry-run only and report-emitting only

## Execute Now

1. Read:
   - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
   - [skill-improver-operator spec](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skill_specs/skill-improver-operator/SKILL.md)
2. Supply:
   - `candidate_code`
   - optional `target_skill_id` from the operator allowlist
3. Keep:
   - `allow_repo_write = false`
   - `do_not_promote = true`

## Quality Gates

- Do not permit repo writeback from this slice.
- Do not widen target selection beyond the explicit allowlist.
- Do not auto-generate candidate code here.
- Do not treat dry-run success as approval for live mutation.
