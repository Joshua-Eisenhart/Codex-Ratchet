---
skill_id: a2-high-intake-graph-builder
name: a2-high-intake-graph-builder
description: Materialize the bounded A2 high-intake owner graph from the live refinery graph after the identity registry scaffold exists.
skill_type: refinement
source_type: repo_skill
applicable_layers: [A2_HIGH_INTAKE]
applicable_graphs: [concept]
inputs: [system_graph_a2_refinery, identity_registry_v1]
outputs: [a2_high_intake_graph_v1, a2_high_intake_graph_audit]
related_skills: [identity-registry-builder, graph-capability-auditor, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded second nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/a2-high-intake-graph-builder/SKILL.md
  gemini: system_v4/skill_specs/a2-high-intake-graph-builder/SKILL.md
  shell: system_v4/skills/a2_high_intake_graph_builder.py
---

# A2 High-Intake Graph Builder

Use this skill when the identity-registry scaffold already exists and the next
bounded task is to materialize the A2 high-intake owner graph.

## Purpose

- create one explicit owner graph for the raw source/extraction layer
- keep the selection rule grounded in current node types and trust zones
- write one audit note alongside the owner graph
- avoid silently drifting into contradiction or kernel layers

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/graphs/identity_registry_v1.json`
2. Include only:
   - `SOURCE_DOCUMENT`
   - `EXTRACTED_CONCEPT`
3. Select nodes only when they match the live high-intake contract:
   - source docs from `INDEX` / `A2_3_INTAKE`
   - extracted concepts from `A2_HIGH_INTAKE` / `A2_3_INTAKE`
4. Include only existing master-graph edges whose endpoints are both selected.
5. Emit:
   - `system_v4/a2_state/graphs/a2_high_intake_graph_v1.json`
   - `system_v4/a2_state/audit_logs/A2_HIGH_INTAKE_GRAPH_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not include refined, kernel, Rosetta, stripped, cartridge, B, SIM, or graveyard nodes.
- Do not promote projection artifacts to authority.
- Do not invent new edge relations; reuse only the ones already present between selected nodes.
