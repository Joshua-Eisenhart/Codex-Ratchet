---
skill_id: a2-skill-improver-target-selector-operator
name: a2-skill-improver-target-selector-operator
description: Audit-only selector for the first bounded target class for skill-improver-operator
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, report_json_path, report_md_path, packet_path]
outputs: [skill_improver_target_selection_report, skill_improver_target_selection_packet]
related_skills: [skill-improver-operator, a2-skill-improver-readiness-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native follow-on slice that turns skill-improver readiness into bounded first-target selection"
adapters:
  codex: system_v4/skill_specs/a2-skill-improver-target-selector-operator/SKILL.md
  shell: system_v4/skills/a2_skill_improver_target_selector_operator.py
---

# A2 Skill Improver Target Selector Operator

Use this skill when `skill-improver-operator` is no longer fully blocked but the
system still needs an explicit first bounded target instead of ad hoc self-mutation.

## Purpose

- read the live readiness gate for `skill-improver-operator`
- rank eligible first targets from the current native skill set
- emit one bounded report + packet
- keep actual mutation outside this slice

## Execute Now

1. Read:
   - [SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json)
   - [skill-improver-operator spec](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skill_specs/skill-improver-operator/SKILL.md)
2. Only select from the bounded first-target class:
   - native maintenance Python skill
   - dedicated smoke exists
   - dedicated codex spec exists
   - propose-only / audit-style behavior
3. Emit:
   - current report
   - compact packet

## Quality Gates

- Do not mutate any target skill here.
- Do not widen to general live repo mutation.
- Do not nominate targets outside the bounded first-target class.
- Keep the output honest even if no eligible target is found.
