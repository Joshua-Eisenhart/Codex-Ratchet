---
skill_id: a2-context-spec-workflow-follow-on-selector-operator
name: a2-context-spec-workflow-follow-on-selector-operator
description: Selector-only follow-on operator that chooses one bounded second slice for the context-spec-workflow-memory cluster without widening into runtime, service, or substrate claims
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs:
  - repo_root
  - selection_scope
  - pattern_report_path
  - pattern_packet_path
  - source_selector_report_path
  - evermem_report_path
  - controller_record_path
  - report_json_path
  - report_md_path
  - packet_path
outputs:
  - a2_context_spec_workflow_follow_on_selector_report
  - a2_context_spec_workflow_follow_on_selector_packet
related_skills:
  - a2-context-spec-workflow-pattern-audit-operator
  - a2-source-family-lane-selector-operator
  - a2-brain-surface-refresher
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "bounded follow-on selector for Context-Engineering, spec-kit, superpowers, and mem0 after the first context/spec/workflow pattern audit"
adapters:
  codex: system_v4/skill_specs/a2-context-spec-workflow-follow-on-selector-operator/SKILL.md
  shell: system_v4/skills/a2_context_spec_workflow_follow_on_selector_operator.py
---

# A2 Context Spec Workflow Follow-On Selector Operator

Use this skill when the first `context-spec-workflow-memory` slice is already
landed and we need one explicit bounded choice about which pattern family to
deepen next.

## Purpose

- read the landed first-slice pattern audit
- choose one bounded follow-on pattern family only
- emit one repo-held report and one compact packet
- keep the result selector-only, non-runtime-live, and non-substrate-replacing

## Execute Now

1. Read:
   - [A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_REPORT__CURRENT__v1.json)
   - [A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_PACKET__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_CONTEXT_SPEC_WORKFLOW_PATTERN_AUDIT_PACKET__CURRENT__v1.json)
   - [A2_SOURCE_FAMILY_LANE_SELECTION_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_SOURCE_FAMILY_LANE_SELECTION_REPORT__CURRENT__v1.json)
   - [A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md)
   - [A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_EVERMEM_BACKEND_REACHABILITY_AUDIT_REPORT__CURRENT__v1.json)
2. Select only one bounded follow-on pattern family.
3. Emit one report and one packet only.

## Quality Gates

- Do not widen into context, specs, workflow, and memory all at once.
- Do not import any runtime, service, or hosted memory assumption.
- Do not claim canonical A2/A1 brain replacement or graph-substrate replacement.
- Do not mutate registry, graph, or external services from this slice.
- Keep the output as a selector recommendation, not a landed second slice.
