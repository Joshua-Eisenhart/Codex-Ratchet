---
skill_id: clifford-edge-semantics-audit
name: clifford-edge-semantics-audit
description: Audit the smallest honest Clifford or geometric-algebra edge-semantics sidecar the current graph stack can support without overclaiming canonical graph ownership or bridge readiness.
skill_type: audit
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL, A2_1_KERNEL, SKILL_REGISTRY]
applicable_graphs: [control, runtime, a2_low_control_graph_v1]
inputs: [a2_low_control_graph_v1, pyg_heterograph_projection_audit_report, toponetx_projection_adapter_audit_report, skill_kernel_link_seeding_policy_audit_report]
outputs: [clifford_edge_semantics_audit_report, clifford_edge_semantics_packet]
related_skills: [pyg-heterograph-projection-audit, toponetx-projection-adapter-audit, skill-kernel-link-seeding-policy-audit]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: [clifford, kingdon]
provenance: "repo-grounded audit slice over whether current graph edges can honestly carry a Clifford or GA sidecar and where that sidecar must remain deferred"
adapters:
  codex: system_v4/skill_specs/clifford-edge-semantics-audit/SKILL.md
  shell: system_v4/skills/clifford_edge_semantics_audit.py
---

# Clifford Edge Semantics Audit

Use this skill when the next graph question is no longer "should we add richer
edge semantics at all?" but "what is the smallest honest Clifford or GA sidecar
the current graph stack can support right now?"

## Purpose

- read the low-control graph, PyG projection audit, TopoNetX sidecar audit, and
  skill-kernel seeding policy audit
- verify the local `clifford` and `kingdon` toolchain works
- measure what current edge attributes can support now
- separate:
  - safe scalar carriers
  - deferred GA payload fields
  - forbidden current uses
- keep GA semantics as a read-only sidecar, not canonical graph ownership

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
   - `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json`
   - `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json`
   - `system_v4/a2_state/audit_logs/SKILL_KERNEL_LINK_SEEDING_POLICY_AUDIT__CURRENT__v1.json`
2. Keep the canonical graph and registry as owner surfaces.
3. Verify the local GA sidecars:
   - `clifford`
   - `kingdon`
4. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not treat Clifford or GA sidecars as canonical graph storage.
- Do not attach GA semantics to `OVERLAPS` while that relation remains quarantined.
- Do not use GA semantics to bypass the current no-auto-seeding rule for `SKILL -> KERNEL_CONCEPT`.
- Keep the result audit-only, proposal-only, and repo-held.
