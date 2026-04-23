---
skill_id: graph-capability-auditor
name: graph-capability-auditor
description: Audit what the current graph substrate can actually express and what it still cannot, grounded in live graph stores, projections, and query surfaces.
skill_type: audit
source_type: repo_skill
applicable_layers: [INDEX, A2_HIGH_INTAKE, A2_MID_REFINEMENT, A2_LOW_CONTROL, A1_JARGONED, A1_STRIPPED, A1_CARTRIDGE]
applicable_graphs: [concept, dependency, rosetta, runtime, attractor]
inputs: [system_graph_a2_refinery, nested_graph_v1, promoted_subgraph, a1_graph_projection]
outputs: [graph_capability_report, graph_capability_note]
related_skills: [ratchet-a2-a1, nested-graph-layer-auditor, ratchet-overseer]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "repo-grounded capability audit for the nested graph stack"
adapters:
  codex: system_v4/skill_specs/graph-capability-auditor/SKILL.md
  gemini: system_v4/skill_specs/graph-capability-auditor/SKILL.md
  shell: system_v4/skills/graph_capability_auditor.py
---

# Graph Capability Auditor

Use this skill when the question is not "what graph do we want?" but "what can
the current graph substrate actually do right now?"

## Purpose

- identify the authoritative live graph store
- identify projections versus true owner surfaces
- report which layer populations exist only inside the monolithic graph
- report which target layer stores are still missing
- report which NetworkX query surfaces exist now
- prevent overclaiming about nested graphs, attractor basins, or axis structures

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/graphs/nested_graph_v1.json`
   - `system_v4/a2_state/graphs/promoted_subgraph.json`
   - `system_v4/a1_state/A1_GRAPH_PROJECTION.json`
2. Treat only the live refinery graph as authoritative.
3. Count layer populations in the live graph.
4. Check whether separate owner stores exist for:
   - `A2_HIGH_INTAKE`
   - `A2_MID_REFINEMENT`
   - `A2_LOW_CONTROL`
   - `A1_JARGONED`
   - `A1_STRIPPED`
   - `A1_CARTRIDGE`
5. Check whether the identity registry exists.
6. Record current query capability, especially relation-filtered NetworkX wrappers.
7. Emit one JSON report and one short markdown note under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not describe a projection as an owner graph.
- Do not describe a layer population as a separate graph store unless the owner file exists.
- Distinguish "queryable in one master graph" from "materialized as a separate layer graph."
