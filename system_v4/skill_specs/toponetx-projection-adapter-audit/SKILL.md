---
skill_id: toponetx-projection-adapter-audit
name: toponetx-projection-adapter-audit
description: Build the first bounded read-only TopoNetX sidecar over the low-control owner graph so higher-order structure can be audited without replacing canonical graph ownership.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_1_KERNEL]
applicable_graphs: [control, a2_low_control_graph_v1]
inputs: [a2_low_control_graph_v1, system_graph_a2_refinery, control_graph_bridge_source_audit_report]
outputs: [toponetx_projection_adapter_audit_report, toponetx_projection_adapter_packet]
related_skills: [a2-low-control-graph-builder, pyg-heterograph-projection-audit, control-graph-bridge-source-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: [toponetx]
provenance: "repo-grounded read-only topological sidecar over the low-control owner graph after bridge-source limits were made explicit"
adapters:
  codex: system_v4/skill_specs/toponetx-projection-adapter-audit/SKILL.md
  shell: system_v4/skills/toponetx_projection_adapter_audit.py
---

# TopoNetX Projection Adapter Audit

Use this skill when the next graph question is no longer "can we install
topological tooling?" but "what is the smallest honest topological sidecar we
can construct over the current kernel/control owner graph without inventing
extra topology?"

## Purpose

- read the bounded low-control owner graph as the first projection surface
- keep the full refinery graph as canonical truth owner
- admit only low-control relations that already behave like meaningful control
  structure
- quarantine preserved `OVERLAPS` edges from equal-weight topological use
- prove one read-only `TopoNetX` cell complex shape
- report candidate higher-order motifs as audit-only observations, not canonical
  cells

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json`
2. Keep the low-control owner graph as the bounded probe surface only.
3. Build one `TopoNetX` cell complex with:
   - `0-cells`: low-control nodes
   - `1-cells`: only `DEPENDS_ON`, `EXCLUDES`, `STRUCTURALLY_RELATED`, `RELATED_TO`
   - `OVERLAPS`: quarantined out of equal-weight topology
   - `2-cells+`: none as canonical emitted truth
4. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not replace the canonical graph owner with the `TopoNetX` sidecar.
- Do not treat `OVERLAPS` as equal-weight topology when the current low-control audit still marks it for quarantine/downranking.
- Do not emit canonical 2-cells from triangles or loops; keep them as candidate motifs only.
- Keep the result audit-only, proposal-only, and repo-held.
