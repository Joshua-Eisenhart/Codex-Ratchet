---
skill_id: pyg-heterograph-projection-audit
name: pyg-heterograph-projection-audit
description: Build a read-only PyG heterograph contract over the current control-facing graph families without changing canonical graph ownership.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_MID_REFINEMENT, B_ADJUDICATED, SIM_EVIDENCED, SKILL_REGISTRY]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs: [system_graph_a2_refinery, a2_low_control_graph_v1]
outputs: [pyg_heterograph_projection_audit_report, pyg_heterograph_projection_packet]
related_skills: [graph-capability-auditor, nested-graph-layer-auditor, a2-next-state-signal-adaptation-audit-operator]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
  requires_tool: true
tool_dependencies: [torch, torch-geometric]
provenance: "read-only projection contract that maps the current control-facing graph families into a first PyG heterograph view"
adapters:
  codex: system_v4/skill_specs/pyg-heterograph-projection-audit/SKILL.md
  shell: system_v4/skills/pyg_heterograph_projection_audit.py
---

# PyG Heterograph Projection Audit

Use this skill when the question is:

- what is the first honest PyTorch Geometric view of the current graph?
- which node families and relation families actually survive projection now?
- what stays deferred because the graph still lacks real bridges?

## Purpose

- keep `pydantic + NetworkX + JSON` as canonical graph truth
- build one bounded read-only PyG heterograph view over the current control-facing families
- prove the data-flow contract before any training or mutation claim
- report what is present, what is absent, and what the next projection follow-on should be

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
2. Keep the canonical live graph store as the owner surface.
3. Use `a2_low_control_graph_v1.json` only as the bounded owner-surface probe.
4. Build a read-only PyG heterograph over the current control-facing families:
   - `KERNEL_CONCEPT`
   - `SKILL`
   - `EXECUTION_BLOCK`
   - `B_OUTCOME`
   - `B_SURVIVOR`
   - `SIM_EVIDENCED`
5. Emit one report and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not claim PyG replaces canonical graph ownership.
- Do not claim the current graph is already one unified control graph if the relation families stay separated.
- Do not claim training is ready from this slice alone.
- Keep the result read-only, audit-only, and proposal-only.
