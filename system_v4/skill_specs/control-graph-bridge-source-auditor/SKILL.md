---
skill_id: control-graph-bridge-source-auditor
name: control-graph-bridge-source-auditor
description: Audit which missing control-graph bridges have honest existing source surfaces and which still remain heuristic-only, so future bridge seeding stays fail-closed.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, B_ADJUDICATED, SIM_EVIDENCED, SKILL_REGISTRY]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs: [system_graph_a2_refinery, control_graph_bridge_gap_audit_report, pyg_heterograph_projection_audit_report]
outputs: [control_graph_bridge_source_audit_report, control_graph_bridge_source_packet]
related_skills: [control-graph-bridge-gap-auditor, pyg-heterograph-projection-audit, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "repo-grounded audit slice over the current source surfaces that could or could not honestly ground control-graph bridge derivation"
adapters:
  codex: system_v4/skill_specs/control-graph-bridge-source-auditor/SKILL.md
  shell: system_v4/skills/control_graph_bridge_source_auditor.py
---

# Control Graph Bridge Source Auditor

Use this skill when the graph gap is already known and the next question is:
"which bridge families can be derived from real owner-bound repo surfaces right
now, and which would still be speculative if we seeded them?"

## Purpose

- read the authoritative live graph plus the current bridge-gap and PyG audits
- distinguish:
  - `heuristic_only`
  - `partial_property_trace`
  - `chain_partial`
  - `not_derivable_now`
- keep skill-side bridge claims fail-closed when only textual or operational
  metadata exists
- surface witness/evidence families that already carry partial kernel traceability
- recommend the next bounded follow-on without widening bridge claims

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_GAP_AUDIT__CURRENT__v1.json`
   - `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json`
2. Keep the canonical live graph store as the owner surface.
3. Measure which bridge families have:
   - direct relation support
   - property-level trace fields
   - chain-level derivation support
   - only heuristic/textual hints
4. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not treat skill text or generic metadata as owner-bound concept identity.
- Do not claim a bridge is derivable if the source field does not resolve into a live kernel concept.
- Do not widen chain-derived witness evidence into direct kernel linkage.
- Keep the result audit-only, proposal-only, and repo-held.
