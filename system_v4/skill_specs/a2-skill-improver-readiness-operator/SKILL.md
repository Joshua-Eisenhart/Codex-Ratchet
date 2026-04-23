---
skill_id: a2-skill-improver-readiness-operator
name: a2-skill-improver-readiness-operator
description: Emit one bounded audit-only repo-held readiness report for skill-improver-operator before treating it as a live repo-mutating meta-skill.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, target_skill_path, report_json_path, report_md_path, packet_path]
outputs: [skill_improver_readiness_report, skill_improver_readiness_packet]
related_skills: [skill-improver-operator, a2-brain-surface-refresher, graph-capability-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "Ratchet-native meta-skill readiness audit over skill-improver-operator before live mutation claims"
adapters:
  codex: system_v4/skill_specs/a2-skill-improver-readiness-operator/SKILL.md
  shell: system_v4/skills/a2_skill_improver_readiness_operator.py
---

# A2 Skill Improver Readiness Operator

Use this skill when we need one bounded truth surface that checks whether
`skill-improver-operator` is actually ready to be treated as a live repo-mutating
meta-skill.

## Purpose

- compare the current registry claims to the real implementation
- verify dispatch wiring and proof surfaces
- emit one repo-held report and one packet
- keep non-goals explicit so audit does not turn into mutation

## Execute Now

1. Read:
   - [V4_SKILL_CLUSTER_SPEC__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_SKILL_CLUSTER_SPEC__CURRENT.md)
   - [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.md)
2. Inspect:
   - [skill_improver_operator.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/skill_improver_operator.py)
   - [skill_registry_v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a1_state/skill_registry_v1.json)
   - [run_real_ratchet.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skills/run_real_ratchet.py)
3. Emit bounded readiness artifacts only.

## Default Outputs

When no explicit paths are supplied, write:

- `system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/SKILL_IMPROVER_READINESS_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not mutate the target skill from this slice.
- Do not claim `skill-improver-operator` is safe for live repo mutation yet.
- Do not count syntax-only compile checks as real target validation.
- Keep this slice audit-only, nonoperative, and explicit about non-promotion.
