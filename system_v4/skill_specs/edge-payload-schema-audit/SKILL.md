---
skill_id: edge-payload-schema-audit
name: edge-payload-schema-audit
description: Audit the smallest honest sidecar schema for richer edge payloads over admitted low-control relations after the Clifford semantics pass, while keeping canonical graph ownership unchanged.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_1_KERNEL]
applicable_graphs: [control, a2_low_control_graph_v1]
inputs: [a2_low_control_graph_v1, toponetx_projection_adapter_audit_report, clifford_edge_semantics_audit_report]
outputs: [edge_payload_schema_audit_report, edge_payload_schema_packet]
related_skills: [clifford-edge-semantics-audit, toponetx-projection-adapter-audit, pyg-heterograph-projection-audit]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "repo-grounded audit slice over the first bounded sidecar schema for richer edge payloads on admitted low-control relations"
adapters:
  codex: system_v4/skill_specs/edge-payload-schema-audit/SKILL.md
  shell: system_v4/skills/edge_payload_schema_audit.py
---

# Edge Payload Schema Audit

Use this skill when the next graph question is no longer "can richer edge
semantics exist?" but "what exact sidecar schema can the current low-control
graph honestly support right now?"

## Purpose

- read the bounded low-control owner graph plus the current TopoNetX and
  Clifford audits
- derive one minimal read-only sidecar schema for admitted edge relations
- separate:
  - required carrier fields
  - optional scalar carriers
  - deferred GA fields
  - forbidden scope
- keep the schema proposal repo-held and nonoperative

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
   - `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json`
   - `system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.json`
2. Keep the canonical graph store unchanged.
3. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not change canonical graph edges or attributes from this slice.
- Do not include `OVERLAPS` in the admitted schema scope.
- Do not include `SKILL` edges in the admitted schema scope.
- Keep the result audit-only, proposal-only, and repo-held.
