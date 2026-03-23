---
skill_id: a2-tracked-work-operator
name: a2-tracked-work-operator
description: Emit one bounded repo-held tracked-work state artifact for the current imported-cluster tranche, using existing queue and audit surfaces instead of inventing a parallel planning substrate.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, report_path]
outputs: [work_state_report]
related_skills: [a2-skill-source-intake-operator, skill-improver-operator]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "lev-os/agents work pattern adapted into a bounded Ratchet tracked-work note"
adapters:
  codex: system_v4/skill_specs/a2-tracked-work-operator/SKILL.md
  shell: system_v4/skills/a2_tracked_work_operator.py
---

# A2 Tracked Work Operator

Use this skill when the current imported-cluster tranche needs one explicit
repo-held work-state artifact over existing queue/audit surfaces.

## Purpose

- keep current slice, next action or explicit no-next-slice, stop/continue, and non-goals explicit
- adapt the useful lifecycle discipline from `work` without importing `.lev/pm`
- use existing Ratchet queue, audit, and session surfaces instead of creating a new planning substrate

## Execute Now

1. Read:
   - [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - [A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json)
   - [SYSTEM_SKILL_BUILD_PLAN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
   - [NESTED_GRAPH_BUILD_QUEUE_STATUS__CURRENT__2026_03_20__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/NESTED_GRAPH_BUILD_QUEUE_STATUS__CURRENT__2026_03_20__v1.md)
   - [doc_queue.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/doc_queue.json)
2. Emit one bounded tracked-work report.
3. Keep the next move explicit and the non-goals explicit.

## Default Outputs

When no explicit path is supplied, write:

- `system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.md`

## Quality Gates

- Do not create `.lev/pm/*` owner surfaces.
- Do not import workflow-skill scaffolding.
- Do not claim the tracked-work cluster is live beyond this bounded note.
- Do not treat this as a replacement for closeout, queue, or A2 owner surfaces.
