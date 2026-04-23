---
skill_id: nested-graph-layer-auditor
name: nested-graph-layer-auditor
description: Audit each queued nested-graph layer against the build program, required boot surfaces, owner surfaces, and actual materialization state.
skill_type: audit
source_type: repo_skill
applicable_layers: [INDEX, A2_HIGH_INTAKE, A2_MID_REFINEMENT, A2_LOW_CONTROL, A1_JARGONED, A1_STRIPPED, A1_CARTRIDGE]
applicable_graphs: [concept, dependency, rosetta]
inputs: [nested_graph_build_program, build_queue_status_packet]
outputs: [nested_graph_layer_audit_report, nested_graph_layer_audit_note]
related_skills: [graph-capability-auditor, ratchet-a2-a1, thread-run-monitor]
capabilities:
  can_write_repo: true
  can_only_propose: true
tool_dependencies: []
provenance: "controller-grade audit for the 3+3 nested graph build queue"
adapters:
  codex: system_v4/skill_specs/nested-graph-layer-auditor/SKILL.md
  gemini: system_v4/skill_specs/nested-graph-layer-auditor/SKILL.md
  shell: system_v4/skills/nested_graph_layer_auditor.py
---

# Nested Graph Layer Auditor

Use this skill to check what the queued 3+3 layer program can honestly claim
today.

## Purpose

- read the repo-held nested graph build program
- inspect required boot, source artifacts, expected outputs, and owner surfaces
- report which layers are materialized, queued, or blocked
- keep the build program honest as the graph stack grows

## Execute Now

1. Load the current nested graph build program JSON.
2. For each build unit:
   - verify required boot surfaces exist
   - verify source artifacts exist
   - verify whether the owner surface already exists
   - count how many expected outputs already exist
3. Classify each unit:
   - `MATERIALIZED`
   - `QUEUED`
   - `BLOCKED`
4. Emit one JSON report and one short markdown note under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not call a layer materialized if its owner surface does not exist.
- Do not silently ignore missing source artifacts or missing boot surfaces.
- Preserve the difference between "queued next" and "blocked by missing prerequisites."
