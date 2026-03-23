---
skill_id: edge-payload-schema-probe
name: edge-payload-schema-probe
description: Build one read-only sidecar payload preview over an admitted low-control relation family using the current edge-payload schema contract, without writing anything back into the canonical graph.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_1_KERNEL]
applicable_graphs: [control, a2_low_control_graph_v1]
inputs: [a2_low_control_graph_v1, edge_payload_schema_audit_report, edge_payload_schema_packet, relation]
outputs: [edge_payload_schema_probe_report, edge_payload_schema_probe_packet]
related_skills: [edge-payload-schema-audit, clifford-edge-semantics-audit, toponetx-projection-adapter-audit]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "repo-grounded read-only probe over one admitted edge-payload schema relation family"
adapters:
  codex: system_v4/skill_specs/edge-payload-schema-probe/SKILL.md
  shell: system_v4/skills/edge_payload_schema_probe.py
---

# Edge Payload Schema Probe

Use this skill when the schema audit is already landed and the next graph
question is: can one admitted relation family be instantiated as a read-only
payload preview without changing canonical graph ownership?

## Purpose

- read the bounded low-control owner graph plus the current edge-payload schema
  audit
- choose one admitted relation family
- emit a small set of read-only payload previews using current carrier fields
  and deferred GA slots
- keep the result sidecar-only, repo-held, and nonoperative

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
   - `system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.json`
   - `system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PACKET__CURRENT__v1.json`
2. Default the first relation probe to `STRUCTURALLY_RELATED` unless an
   explicit relation override is provided.
3. Emit one JSON report, one markdown note, and one compact packet under
   `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not write these payloads into the canonical graph.
- Do not include `OVERLAPS` or `SKILL` edge families in probe scope.
- Keep deferred GA fields as empty slots or `null` placeholders, not claimed
  semantics.
- Keep the result audit-only, proposal-only, and repo-held.
