---
skill_id: a2-mid-refinement-graph-builder
name: a2-mid-refinement-graph-builder
description: Materialize the bounded A2 mid-refinement owner graph from the live refinery graph after the identity and A2 high-intake owner graphs exist.
skill_type: refinement
source_type: repo_skill
applicable_layers: [A2_MID_REFINEMENT]
applicable_graphs: [concept]
inputs: [system_graph_a2_refinery, identity_registry_v1, a2_high_intake_graph_v1]
outputs: [a2_mid_refinement_graph_v1, a2_mid_refinement_graph_audit]
related_skills: [identity-registry-builder, a2-high-intake-graph-builder, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded third nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/a2-mid-refinement-graph-builder/SKILL.md
  gemini: system_v4/skill_specs/a2-mid-refinement-graph-builder/SKILL.md
  shell: system_v4/skills/a2_mid_refinement_graph_builder.py
---

# A2 Mid-Refinement Graph Builder

Use this skill when the identity and A2 high-intake scaffolds exist and the
next bounded task is to materialize the contradiction/refinement owner graph.

## Purpose

- create one explicit owner graph for live refined candidates
- keep the boundary on active A2-2 candidates, not promoted kernels or retired graveyard nodes
- write one audit note alongside the owner graph

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/graphs/identity_registry_v1.json`
   - `system_v4/a2_state/graphs/a2_high_intake_graph_v1.json`
2. Include only `REFINED_CONCEPT` nodes with `trust_zone == A2_2_CANDIDATE`.
3. Include only existing master-graph edges whose endpoints are both selected.
4. Emit:
   - `system_v4/a2_state/graphs/a2_mid_refinement_graph_v1.json`
   - `system_v4/a2_state/audit_logs/A2_MID_REFINEMENT_GRAPH_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not include `KERNEL_CONCEPT` promoted into `A2_1_KERNEL`.
- Do not include retired `GRAVEYARD` refined nodes or thread seals.
- Do not treat promoted_subgraph or contradiction notes as authority for membership.
