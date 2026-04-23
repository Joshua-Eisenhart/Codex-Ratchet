---
skill_id: a2-context-spec-workflow-post-shell-selector-operator
name: a2-context-spec-workflow-post-shell-selector-operator
description: Selector-only post-shell controller slice for the context-spec-workflow-memory cluster that holds the lane after append-safe landing and records the first standby follow-on without widening by momentum
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, selection_scope, append_safe_report_path, follow_on_selector_report_path, evermem_report_path, report_json_path, report_md_path, packet_path]
outputs: [a2_context_spec_workflow_post_shell_selector_report, a2_context_spec_workflow_post_shell_selector_packet]
related_skills: [a2-append-safe-context-shell-audit-operator, a2-context-spec-workflow-follow-on-selector-operator, a2-brain-surface-refresher]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "bounded post-shell selector for the context-spec-workflow-memory cluster after the append-safe continuity-shell slice"
adapters:
  codex: system_v4/skill_specs/a2-context-spec-workflow-post-shell-selector-operator/SKILL.md
  shell: system_v4/skills/a2_context_spec_workflow_post_shell_selector_operator.py
---

# A2 Context Spec Workflow Post Shell Selector Operator

Use this skill when the `context-spec-workflow-memory` cluster has already landed
its append-safe continuity-shell slice and the controller needs one explicit
post-shell hold-or-standby result.

## Purpose

- confirm the append-safe slice actually landed cleanly
- keep the cluster held by default after that landing
- record the first standby follow-on without opening it by momentum
- preserve explicit non-goals around multi-pattern widening, runtime import,
  service bootstrap, canonical brain replacement, graph replacement, and
  memory-platform ownership

## Execute Now

1. Confirm the append-safe slice report is green.
2. Confirm the older follow-on selector still points at the append-safe slice.
3. Emit one repo-held post-shell selector report and one compact packet.
4. Keep the current cluster held unless a future explicit reselection reopens it.

## Quality Gates

- No direct landing of another pattern family from this selector.
- No multi-pattern widening.
- No runtime/service/training claims.
- No canonical `A2` / `A1` brain replacement claim.
- No graph-substrate replacement claim.
- No memory-platform ownership claim.
