---
skill_id: a2-workshop-analysis-gate-operator
name: a2-workshop-analysis-gate-operator
description: Emit one bounded repo-held workshop-analysis gate report for a single imported candidate, without claiming POC, integration, or full lev workshop import.
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, candidate, candidate_path, intake_context_path, source_refs, report_path, markdown_path, packet_path]
outputs: [workshop_analysis_gate_report, workshop_analysis_gate_packet]
related_skills: [a2-skill-source-intake-operator, a2-tracked-work-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "lev-os/agents lev-workshop + lev-align + work retooled into a bounded Ratchet workshop-analysis gate slice"
adapters:
  codex: system_v4/skill_specs/a2-workshop-analysis-gate-operator/SKILL.md
  shell: system_v4/skills/a2_workshop_analysis_gate_operator.py
---

# A2 Workshop Analysis Gate Operator

Use this skill when one imported workshop candidate needs a bounded analysis/gate
verdict before anyone claims a later POC or integration slice should exist.

## Purpose

- analyze exactly one candidate
- apply a small pass/warn/block gate set over current repo-held evidence
- emit one repo-held report and one compact packet
- keep non-goals explicit so this does not turn into a fake full-workshop import

## Execute Now

1. Read:
   - [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
   - [A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json)
   - [A2_TRACKED_WORK_STATE__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json)
   - [A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json)
   - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
2. Inspect the single candidate and its local source refs.
3. Emit one gate report and one compact packet only.

## Default Outputs

When no explicit paths are supplied, write:

- `system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1.md`
- `system_v4/a2_state/audit_logs/A2_WORKSHOP_ANALYSIS_GATE_PACKET__CURRENT__v1.json`

## Quality Gates

- Do not build a POC here.
- Do not claim integration or production promotion.
- Do not import `.lev/workshop`, `.lev/pm`, or `.lev/validation-gates.yaml`.
- Do not claim the full `lev-workshop`, `lev-align`, or `work` systems are ported.
- Keep this slice audit-only, nonoperative, and explicit about non-promotion.
