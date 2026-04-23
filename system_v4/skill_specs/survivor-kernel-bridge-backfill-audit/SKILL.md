---
skill_id: survivor-kernel-bridge-backfill-audit
name: survivor-kernel-bridge-backfill-audit
description: Audit whether any B_SURVIVOR nodes can honestly receive direct KERNEL_CONCEPT bridge backfills under current repo truth, or whether direct backfill would overclaim.
skill_type: audit
source_type: repo_skill
applicable_layers: [B_ADJUDICATED, A2_LOW_CONTROL, SIM_EVIDENCED]
applicable_graphs: [runtime, control, a2_low_control_graph_v1]
inputs: [system_graph_a2_refinery, control_graph_bridge_source_audit_report]
outputs: [survivor_kernel_bridge_backfill_audit_report, survivor_kernel_bridge_backfill_packet]
related_skills: [control-graph-bridge-source-auditor, control-graph-bridge-gap-auditor, toponetx-projection-adapter-audit]
capabilities:
  can_write_repo: true
  can_only_propose: true
  reads_graph: true
tool_dependencies: []
provenance: "repo-grounded audit slice over whether survivor-side direct kernel bridge backfill is actually justified under current graph truth"
adapters:
  codex: system_v4/skill_specs/survivor-kernel-bridge-backfill-audit/SKILL.md
  shell: system_v4/skills/survivor_kernel_bridge_backfill_audit.py
---

# Survivor Kernel Bridge Backfill Audit

Use this skill when the witness-side bridge question is no longer "do survivors
carry any kernel-facing trace at all?" but "can we honestly backfill more direct
`B_SURVIVOR -> KERNEL_CONCEPT` edges right now?"

## Purpose

- read the authoritative live graph plus the current bridge-source audit
- classify survivor `source_concept_id` targets by live target class
- distinguish:
  - already-satisfied direct kernel links
  - direct kernel links that would be backfillable now
  - survivor links that already land on non-kernel concept classes
  - survivors with no usable source target
- keep direct kernel backfill fail-closed when survivors only resolve to
  `REFINED_CONCEPT` or `EXTRACTED_CONCEPT`

## Execute Now

1. Load:
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
   - `system_v4/a2_state/audit_logs/CONTROL_GRAPH_BRIDGE_SOURCE_AUDIT__CURRENT__v1.json`
2. Keep the canonical live graph store as the owner surface.
3. Measure all `B_SURVIVOR` nodes against:
   - `properties.source_concept_id`
   - existing `ACCEPTED_FROM` edges
   - resolved live target `node_type`
4. Emit one JSON report, one markdown note, and one compact packet under `system_v4/a2_state/audit_logs/`.

## Quality Gates

- Do not promote a survivor’s `source_concept_id` to a kernel link when it resolves only to `REFINED_CONCEPT` or `EXTRACTED_CONCEPT`.
- Do not count already-present direct kernel links as backfill candidates.
- Do not mutate the graph from this slice.
- Keep the result audit-only, proposal-only, and repo-held.
