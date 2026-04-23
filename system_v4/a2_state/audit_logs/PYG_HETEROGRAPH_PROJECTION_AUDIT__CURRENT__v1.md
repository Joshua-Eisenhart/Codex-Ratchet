# PyG Heterograph Projection Audit

- generated_utc: `2026-03-22T03:39:03Z`
- status: `ok`
- projection_id: `PYG_PROJECTION::control_subgraph_v1`
- projection_focus: `read_only_control_subgraph`
- canonical_graph_owner: `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
- bounded_probe_source: `system_v4/a2_state/graphs/a2_low_control_graph_v1.json`
- audit_only: `True`
- do_not_promote: `True`

## Node Contract
- `B_OUTCOME`: 401 nodes
- `B_SURVIVOR`: 78 nodes
- `EXECUTION_BLOCK`: 401 nodes
- `KERNEL_CONCEPT`: 842 nodes
- `SIM_EVIDENCED`: 67 nodes
- `SKILL`: 123 nodes

## Edge Contract
- `B_OUTCOME::ADJUDICATED_FROM::EXECUTION_BLOCK`: 401 edges
- `B_SURVIVOR::ACCEPTED_FROM::KERNEL_CONCEPT`: 1 edges
- `KERNEL_CONCEPT::CONTRADICTS::KERNEL_CONCEPT`: 1 edges
- `KERNEL_CONCEPT::DEPENDS_ON::KERNEL_CONCEPT`: 380 edges
- `KERNEL_CONCEPT::EXCLUDES::KERNEL_CONCEPT`: 101 edges
- `KERNEL_CONCEPT::REFINED_INTO::KERNEL_CONCEPT`: 10 edges
- `KERNEL_CONCEPT::RELATED_TO::KERNEL_CONCEPT`: 233 edges
- `KERNEL_CONCEPT::STRUCTURALLY_RELATED::KERNEL_CONCEPT`: 726 edges
- `SIM_EVIDENCED::SIM_EVIDENCE_FOR::B_SURVIVOR`: 67 edges
- `SKILL::RELATED_TO::SKILL`: 295 edges
- `SKILL::SKILL_FOLLOWS::SKILL`: 12 edges

## Observed Limits
- skill nodes currently project as a separate relation family; direct skill-to-kernel bridges are not materially present
- B_OUTCOME currently connects to EXECUTION_BLOCK, not directly to the kernel concept graph
- SIM_EVIDENCED currently connects to B_SURVIVOR, so witness evidence is present but not yet unified into the kernel/skill slice

## Recommended Next Actions
- Keep canonical graph ownership in the JSON-backed live graph store.
- Use this projection as a read-only PyG view over the control-facing families only.
- Add a separate graph-bridge audit for skill-to-kernel and witness-to-kernel links before any training claim.
- Treat TopoNetX as the next higher-order projection lane rather than widening this PyG slice into full topology ownership.

## Issues
- none
