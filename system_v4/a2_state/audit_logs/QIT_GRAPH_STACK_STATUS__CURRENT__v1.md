# QIT Graph Stack Status

- status: `precheck_blocked`
- generated_utc: `2026-03-30T11:04:54Z`
- purpose: `read-only-by-default verification surface over the current QIT owner snapshot and bounded sidecars`
- snapshot_id: `ae9951d07249376c52a1c57b8f0f2ceefd9116f1eee944074cb28791561e4393`
- git_sha: `56e79ea13dac0552c8ec43f6fa7da2e55c764e44`
- git_worktree_dirty: `True`
- owner_builder_sha256: `e28d9102328a55222cdfaf58db179f1539de8d21192883022a1c24d2eb708f90`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- tracked_report_files: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.json, /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.md`
- tracked_report_files_dirty_before_generation: `[' M system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.json', ' M system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.md']`
- write_report_required_for_refresh: `True`

## Owner Layer
- qit_graph_json: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.json`
- qit_graph_action: `read_existing_snapshot`
- qit_graph_sha256: `b49b52d5d8d9c406ea6e6ac1cbf7b029f517b8d692cd320171f15ebd607a7fed`
- qit_graph_content_hash: `585499a4d13298615601af806cf9c0d01f56ef6e47879c5c82abf39227ef373a`
- qit_graph_content_hash_matches_recomputed: `True`
- graphml_export: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.graphml`
- graphml_action: `read_existing_snapshot`
- graphml_sha256: `0158f9197931ebf7f6e2938b37ace7a4fb7eae81924d406487ef6faab6125373`
- node_count: `105`
- edge_count: `272`
- live_node_types: `AXIS, ENGINE, MACRO_STAGE, NEG_WITNESS, OPERATOR, SUBCYCLE_STEP, TORUS`
- schema_ready_not_instantiated: `WEYL_BRANCH`

## Verification Scope
- mutates_owner_truth: `False`
- mutates_graphml_sidecar: `False`
- verifies:
- owner snapshot file presence, schema tag, counts, and file hash
- embedded owner content_hash against a recomputed canonical hash
- existing GraphML snapshot hash and parseability when present, or explicit missing status when absent
- sidecar availability and projection summaries over the loaded owner snapshot
- existing runtime evidence bridge presence and owner-snapshot alignment when present
- existing bounded retrieval sidecar presence and safety flags when present
- existing Hopf/Weyl carrier projection presence and owner-snapshot alignment when present
- existing Hopf/Weyl evidence audit presence and owner-snapshot alignment when present
- existing torus/type repair-gap report presence and owner-snapshot alignment when present
- coarse promotion-gate state for owner structure, cross-layer alignment, runtime state, and history graph presence
- does_not_verify:
- that the owner graph matches docs or runtime semantics beyond the stored snapshot
- that the existing GraphML snapshot is fresh unless it was explicitly refreshed in this run
- that a present runtime evidence bridge constitutes a promoted runtime-state or history graph
- that a present retrieval sidecar constitutes embedding-backed LightRAG retrieval or owner-authoritative memory
- that a present Hopf/Weyl projection constitutes promoted torus 2-cells, instantiated Weyl branches, or validated spinor semantics
- that a present Hopf/Weyl evidence audit constitutes promotion evidence or validated live Weyl branch semantics
- that a present torus/type repair-gap report constitutes repair completion or promotion evidence
- that sidecar outputs are promotion-ready owner truth
- that any blocked promotion gate should be auto-promoted or auto-repaired
- that a PRECHECK_OK promotion gate satisfies the negative-proof, round-trip, no-sidecar-read, or human-audit requirements from the promotion-gates doc

## Promotion Gates
- gate_status_meaning: `PRECHECK_OK/PRECHECK_MISSING are coarse readiness checks only, not full promotion completion`
- owner_structure_gate: `PRECHECK_OK`
- cross_layer_alignment_gate: `PRECHECK_OK`
- runtime_state_gate: `PRECHECK_MISSING`
- history_graph_gate: `PRECHECK_MISSING`

## Sidecars
- preferred sidecar interpreter: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/.venv_spec_graph/bin/python`
- preferred sidecar interpreter exists: `True`
- TopoNetX available (current interpreter): `False`
- TopoNetX importable (preferred interpreter): `True`
- TopoNetX shape: `[]`
- clifford available (current interpreter): `False`
- clifford importable (preferred interpreter): `True`
- kingdon available (current interpreter): `False`
- kingdon importable (preferred interpreter): `True`
- PyG available (current interpreter): `False`
- PyG importable (preferred interpreter): `True`
- LightRAG status: `registered_not_integrated`

## Runtime Evidence Bridge
- status: `partial`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md`
- owner_content_hash_matches_current_snapshot: `True`
- runtime_sample_count: `2`
- sim_packet_count: `5`
- complete_mappings: `3`
- partial_mappings: `2`
- axis0_surface_status: `read_only_control_plane_summary_only`
- axis0_runtime_sample_count: `2`
- axis0_direct_bridge_families: `['Xi_LR_direct_control']`
- axis0_history_window_bridge_families: `['Xi_hist_window_control']`
- axis0_history_window_sample_counts: `[32]`

## Retrieval Sidecar
- status: `present`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RETRIEVAL_SIDECAR__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RETRIEVAL_SIDECAR__CURRENT__v1.md`
- mode: `lexical_fallback_only`
- retrieval_role: `context_only_non_authoritative`
- allow_owner_writes: `False`
- allow_proof_claims: `False`
- embedding_backed_query: `False`
- document_count: `34`
- top_hit_count: `8`

## Hopf/Weyl Projection
- status: `present`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.md`
- owner_content_hash_matches_current_snapshot: `True`
- audit_only: `True`
- observer_only: `True`
- do_not_promote: `True`
- stage_count: `16`
- torus_carrier_count: `3`
- weyl_projection_status: `engine_pair_only_derived`

## Hopf/Weyl Evidence Audit
- status: `present`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.md`
- owner_content_hash_matches_current_snapshot: `True`
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- runtime_alignment_status: `partially_aligned`
- torus_witness_count: `2`
- chirality_witness_count: `2`

## Torus/Type Repair Gap Report
- status: `partial`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_TORUS_TYPE_REPAIR_GAP_REPORT__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_TORUS_TYPE_REPAIR_GAP_REPORT__CURRENT__v1.md`
- owner_content_hash_matches_current_snapshot: `False`
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- torus_gap_count: `3`
- type_gap_count: `3`
- interpretation: `bounded repair map only; listed gaps are not already repaired and this surface is not promotion evidence`

## Next Actions
- keep owner verification read-only by default and use refresh flags only for intentional artifact regeneration
- treat snapshot_id plus file hashes as the join key for future audit/report surfaces
- admit explicit QIT bridge links through the registry before claiming nested-graph integration beyond summary-level presence
- persist and expand the read-only runtime evidence bridge before promoting runtime/history semantics inward
- use the bounded retrieval sidecar as context only until embedding-backed LightRAG query is configured and explicitly kept non-authoritative
- treat the Hopf/Weyl projection as a bounded carrier map only; do not infer promoted torus 2-cells or live Weyl branches from its presence
- treat the Hopf/Weyl evidence audit as a bounded audit surface only; do not treat it as promotion evidence
- treat the torus/type repair-gap report as a bounded repair map only; do not treat listed gaps as already repaired
- promote torus/chirality/runtime semantics only after negative-proof and round-trip gates are satisfied
