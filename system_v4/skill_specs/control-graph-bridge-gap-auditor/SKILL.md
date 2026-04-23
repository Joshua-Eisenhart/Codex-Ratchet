---
skill_id: control-graph-bridge-gap-auditor
name: control-graph-bridge-gap-auditor
description: Audit the missing and weak bridge families inside the current control-facing graph so the next graph tranche targets real gaps instead of imagined ones.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_MID_REFINEMENT, B_ADJUDICATED, SIM_EVIDENCED, SKILL_REGISTRY]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs: [system_graph_a2_refinery, pyg_heterograph_projection_audit_report]
outputs: [control_graph_bridge_gap_audit_report, control_graph_bridge_gap_packet]
related_skills: [graph-capability-auditor, pyg-heterograph-projection-audit, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "repo-grounded audit slice over the current control-facing graph bridge gaps after the first bounded PyG projection"
adapters:
  codex: system_v4/skill_specs/control-graph-bridge-gap-auditor/SKILL.md
  shell: system_v4/skills/control_graph_bridge_gap_auditor.py
---

# Control Graph Bridge Gap Auditor

Use this skill when the graph question is no longer “what can we project?” but
“which control-facing bridge families are actually missing or too weak to make
the graph behave like one joined control substrate?”

## Purpose

- read the authoritative live graph and the current PyG projection audit
- measure the bridge families between:
  - `SKILL`
  - `KERNEL_CONCEPT`
  - `EXECUTION_BLOCK`
  - `B_OUTCOME`
  - `B_SURVIVOR`
  - `SIM_EVIDENCED`
- classify each bridge family as:
  - `missing`
  - `weak_signal`
  - `present`
- recommend the next bounded bridge-focused follow-on instead of widening graph claims

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json`
2. Keep the canonical live graph store as the owner surface.
3. Measure actual cross-family edges in the control-facing subgraph.
4. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not treat desired bridge families as present when the graph does not carry them.
- Do not collapse weak-signal bridges into “solved.”
- Do not claim training readiness from this slice.
- Keep the result audit-only, proposal-only, and repo-held.
