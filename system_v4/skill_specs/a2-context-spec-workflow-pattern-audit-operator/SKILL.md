---
skill_id: a2-context-spec-workflow-pattern-audit-operator
name: a2-context-spec-workflow-pattern-audit-operator
description: Audit-only first slice for the context-spec-workflow-memory cluster that maps append-safe context, executable spec coupling, workflow discipline, and scoped memory-sidecar patterns onto current Ratchet seams
skill_type: maintenance
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT, A2_LOW_CONTROL]
applicable_graphs: [runtime, control, a2_mid_refinement_graph_v1]
inputs: [repo_root, analysis_scope, report_json_path, report_md_path, packet_path]
outputs: [a2_context_spec_workflow_pattern_audit_report, a2_context_spec_workflow_pattern_audit_packet]
related_skills: [a2-source-family-lane-selector-operator, a2-skill-source-intake-operator, a2-research-deliberation-operator]
capabilities:
  can_write_repo: false
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "Ratchet-native first bounded slice for Context-Engineering, spec-kit, superpowers, and mem0 as source-family pressure only"
adapters:
  codex: system_v4/skill_specs/a2-context-spec-workflow-pattern-audit-operator/SKILL.md
  shell: system_v4/skills/a2_context_spec_workflow_pattern_audit_operator.py
---

# A2 Context Spec Workflow Pattern Audit Operator

Use this skill when the selected `context-spec-workflow-memory` lane needs one
first bounded Ratchet-native slice.

## Purpose

- audit local source pressure from:
  - `Context-Engineering`
  - `spec-kit`
  - `superpowers`
  - `mem0`
- keep only the smallest honest pattern families for Ratchet:
  - append-safe context shells
  - executable spec coupling
  - workflow/review discipline
  - scoped memory-sidecar patterns
- map those patterns onto current Ratchet seams without importing the source runtimes

## Execute Now

1. Confirm the four local source repos exist.
2. Keep the slice audit-only and nonoperative.
3. Emit one repo-held report and one compact packet.
4. Preserve explicit non-goals around runtime import, canonical-brain replacement, live automation, and graph-substrate replacement.

## Quality Gates

- No runtime/service/bootstrap import.
- No canonical `A2` / `A1` brain replacement claim.
- No live automation or subagent-orchestrator replacement claim.
- No graph-substrate replacement claim.
- No selector widening by momentum.
