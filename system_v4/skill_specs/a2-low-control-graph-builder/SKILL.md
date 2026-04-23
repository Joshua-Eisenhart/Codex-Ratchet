---
skill_id: a2-low-control-graph-builder
name: a2-low-control-graph-builder
description: Materialize the bounded A2 low-control owner graph from the live refinery graph after the upstream A2 owner graphs exist.
skill_type: refinement
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL]
applicable_graphs: [dependency]
inputs: [system_graph_a2_refinery, identity_registry_v1, a2_high_intake_graph_v1, a2_mid_refinement_graph_v1]
outputs: [a2_low_control_graph_v1, a2_low_control_graph_audit]
related_skills: [identity-registry-builder, a2-high-intake-graph-builder, a2-mid-refinement-graph-builder, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded fourth nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/a2-low-control-graph-builder/SKILL.md
  gemini: system_v4/skill_specs/a2-low-control-graph-builder/SKILL.md
  shell: system_v4/skills/a2_low_control_graph_builder.py
---

# A2 Low-Control Graph Builder

Use this skill when the upstream A2 scaffolds exist and the next bounded task
is to materialize the active kernel/control owner graph.

## Purpose

- create one explicit owner graph for live kernel concepts
- keep the boundary on active `A2_1_KERNEL` concepts, not retired graveyard kernels
- write one audit note alongside the owner graph

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/graphs/identity_registry_v1.json`
   - `system_v4/a2_state/graphs/a2_high_intake_graph_v1.json`
   - `system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json`
2. Include only `KERNEL_CONCEPT` nodes with `trust_zone == A2_1_KERNEL`.
3. Include only existing master-graph edges whose endpoints are both selected.
4. Emit:
   - `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
   - `system_v4/a2_state/audit_logs/A2_LOW_CONTROL_GRAPH_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not include graveyard-retired kernels.
- Do not cross the A1 boundary in this pass.
- Do not infer topology or Rosetta semantics beyond the current kernel slice.
