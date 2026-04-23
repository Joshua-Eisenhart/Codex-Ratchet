---
skill_id: a1-jargoned-graph-builder
name: a1-jargoned-graph-builder
description: Materialize the bounded A1 jargoned owner graph from packet-backed Rosetta fuel, or fail closed when the queued A1 scope does not align with live Rosetta anchors.
skill_type: refinement
source_type: repo_skill
applicable_layers: [A1_JARGONED]
applicable_graphs: [rosetta]
inputs: [system_graph_a2_refinery, rosetta_v2, a1_queue_candidate_registry, a2_to_a1_family_slice]
outputs: [a1_jargoned_graph_v1, a1_jargoned_graph_audit]
related_skills: [identity-registry-builder, a2-low-control-graph-builder, graph-capability-auditor, nested-graph-layer-auditor, a1-rosetta-stripper]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded fifth nested-graph build unit"
adapters:
  codex: system_v4/skill_specs/a1-jargoned-graph-builder/SKILL.md
  gemini: system_v4/skill_specs/a1-jargoned-graph-builder/SKILL.md
  shell: system_v4/skills/a1_jargoned_graph_builder.py
---

# A1 Jargoned Graph Builder

Use this skill when the A2-side owner graphs are in place and the next bounded
task is to materialize the A1 jargoned owner graph from live Rosetta packets.

## Purpose

- build one explicit owner surface for packet-backed A1 jargon/Rosetta nodes
- obey the queued A2->A1 scope instead of pulling from the whole graph
- fail closed if the queue scope and live Rosetta anchors do not align

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a1_state/rosetta_v2.json`
   - `system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`
   - the queued A1-jargoned launch handoff
2. Include only Rosetta packets with:
   - non-empty `source_concept_id`
   - source anchor present in the live master graph
   - `source_term` inside the queued A1 scope
3. Do not materialize inherited A2/master edges into A1_JARGONED.
4. Emit:
   - `system_v4/a1_state/a1_jargoned_graph_v1.json`
   - `system_v4/a2_state/audit_logs/A1_JARGONED_GRAPH_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not treat `A1_GRAPH_PROJECTION.json` as an owner surface.
- Do not infer lexical Rosetta graph edges.
- If the selected family slice and declared handoff slice disagree, fail closed.
- If no queue-scoped packet-backed Rosetta nodes exist, fail closed.
