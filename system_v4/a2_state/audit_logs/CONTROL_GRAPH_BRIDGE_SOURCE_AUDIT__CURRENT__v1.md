# Control Graph Bridge Source Audit

- generated_utc: `2026-03-21T23:34:15Z`
- status: `ok`
- audit_only: `True`
- do_not_promote: `True`
- authoritative_graph: `system_v4/a2_state/graphs/system_graph_a2_refinery.json`

## Source Rows
### SKILL -> KERNEL_CONCEPT
- derivation_status: `heuristic_only`
- current_direct_edge_count: `0`
- grounding_surface: skill nodes currently expose operational metadata such as source_path, applicable layers, inputs, outputs, adapters, and related_skills, but not owner-bound kernel concept identity
- recommended_interpretation: do not seed skill-to-kernel edges from current skill metadata alone; any link would still be heuristic or text-derived

### B_SURVIVOR -> KERNEL_CONCEPT
- derivation_status: `partial_property_trace`
- current_direct_edge_count: `1`
- grounding_surface: B_SURVIVOR.properties.source_concept_id is the strongest current owner-bound kernel trace field
- recommended_interpretation: treat survivor-to-kernel linkage as partially derivable from survivor properties, but only resolved live kernel ids are strong enough for backfill candidates

### SIM_EVIDENCED -> KERNEL_CONCEPT
- derivation_status: `chain_partial`
- current_direct_edge_count: `0`
- grounding_surface: SIM_EVIDENCED reaches kernel-facing trace only through SIM_EVIDENCE_FOR -> B_SURVIVOR -> source_concept_id
- recommended_interpretation: permit only chain-derived kernel trace on the SIM side; do not claim direct sim-to-kernel linkage from current owner surfaces

### B_OUTCOME -> KERNEL_CONCEPT
- derivation_status: `not_derivable_now`
- current_direct_edge_count: `0`
- grounding_surface: B_OUTCOME currently lacks owner-bound kernel trace fields in the live graph
- recommended_interpretation: treat b_outcome nodes as kernel-untraced control-chain surfaces until explicit concept linkage is emitted

### EXECUTION_BLOCK -> KERNEL_CONCEPT
- derivation_status: `not_derivable_now`
- current_direct_edge_count: `0`
- grounding_surface: EXECUTION_BLOCK currently lacks owner-bound kernel trace fields in the live graph
- recommended_interpretation: treat execution_block nodes as kernel-untraced control-chain surfaces until explicit concept linkage is emitted

## Recommended Next Actions
- Do not auto-seed SKILL -> KERNEL_CONCEPT links from current skill metadata; the live owner surfaces still lack owner-bound kernel concept identity on the skill side.
- Treat B_SURVIVOR.properties.source_concept_id as the strongest current witness-side bridge source, but only resolved live kernel ids are strong enough for any backfill proposal.
- Treat SIM_EVIDENCED kernel trace as chain-derived only through SIM_EVIDENCE_FOR -> B_SURVIVOR, not as direct sim-to-kernel linkage.
- Keep B_OUTCOME and EXECUTION_BLOCK kernel-untraced until explicit kernel trace fields or relations are emitted.
- Proceed to the first bounded TopoNetX projection with these bridge-source limits explicit instead of pretending the control graph is already fully joined.

## Issues
- none
