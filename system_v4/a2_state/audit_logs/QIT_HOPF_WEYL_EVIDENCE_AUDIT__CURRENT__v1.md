# QIT Hopf/Weyl Evidence Audit

- status: `bounded_evidence_audit_only`
- generated_utc: `2026-03-29T09:18:26Z`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace Hopf/Weyl evidence audit state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `b4426398c08056ecb7d62fcb2c9c0acb06d8a06b`

## Audit Boundary
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- promotion_claim: `none`

## Owner Snapshot
- qit_graph_schema: `QIT_ENGINE_GRAPH_v2`
- qit_graph_content_hash: `585499a4d13298615601af806cf9c0d01f56ef6e47879c5c82abf39227ef373a`
- node_count: `105`
- edge_count: `272`

## Owner Carrier Evidence
- torus_carrier_count: `3`
- torus_nesting_edge_count: `2`
- stage_on_torus_edge_count: `32`
- owner_missing_anchors: `WEYL_BRANCH`

## Runtime Bridge Alignment
- alignment_status: `partially_aligned`
- owner_hash_matches: `False`
- aligned_engine_public_ids: `qit::ENGINE::type1_deductive, qit::ENGINE::type2_inductive`
- unresolved_links: `0`

## Relevant Negative Evidence
- torus_witnesses: `2`
- chirality_witnesses: `2`
- runtime_bridge_mapped_witnesses: `qit::NEG_WITNESS::neg_axis6_shared, qit::NEG_WITNESS::neg_missing_fe, qit::NEG_WITNESS::neg_missing_operator, qit::NEG_WITNESS::neg_native_only, qit::NEG_WITNESS::neg_type_flatten`

## Candidate Sidecar Evidence
- cell_complex_status: `candidate_projection_only`
- cell_complex_available: `True`
- chirality_mapping_status: `candidate_projection_only`
- chirality_mapping_available: `True`

## Carrier Evidence Summary
- status: `bounded_owner_linked_summary_only`
- promotion_claim: `none`
- torus_public_ids: `qit::TORUS::inner, qit::TORUS::clifford, qit::TORUS::outer`
- torus_negative_witnesses: `qit::NEG_WITNESS::neg_no_torus_transport, qit::NEG_WITNESS::neg_torus_scrambled`
- engine_public_ids: `qit::ENGINE::type1, qit::ENGINE::type2`
- type_split_negative_witnesses: `qit::NEG_WITNESS::neg_no_chirality, qit::NEG_WITNESS::neg_type_flatten`

## Evidence Limits
- not owner truth
- not runtime-state graph
- not history graph
- not live Weyl branch evidence
- not promotion evidence

## Audit Conclusion
- summary: The current QIT lane has live owner torus/chirality scaffold plus aligned bounded sidecars and runtime packets. It supports a bounded carrier-map reading, not promoted Hopf/Weyl semantics.
- safe_now:
  - three torus owner nodes are live: inner, clifford, outer
  - the owner graph carries a two-edge torus nesting chain
  - the owner graph carries thirty-two STAGE_ON_TORUS assignments
  - the owner graph carries two engine nodes and one CHIRALITY_COUPLING edge
  - the Hopf/Weyl sidecar is aligned to the current owner content hash
  - the runtime bridge is aligned to the current owner content hash
- missing_now:
  - no live WEYL_BRANCH owner nodes
  - no promoted torus 2-cells in owner truth
  - no promoted spinor-state graph
  - no promoted runtime-state graph
  - no promoted history graph
- forbidden_claims_now:
  - do not claim live Weyl branch semantics in owner truth
  - do not claim torus 2-cells are promoted owner structure
  - do not claim runtime bridge packets are runtime/history graphs
  - do not claim sidecar candidate mappings are promotion evidence by themselves
