# QIT Graph Stack Status

- status: `precheck_blocked`
- generated_utc: `2026-03-26T23:19:57Z`
- purpose: `read-only-by-default verification surface over the current QIT owner snapshot and bounded sidecars`
- snapshot_id: `6a2086366982c4f43a713ecd1b0286ee67a3625d7eed0520acd199f9b92b23ab`
- git_sha: `0f724e56f67f24d7a7402e568e3c3658eb2b56c2`
- owner_builder_sha256: `271e5c1681d077ea0994fdd4a5a9ff68e0a21e45e4129943e03858b0e4744822`

## Owner Layer
- qit_graph_json: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.json`
- qit_graph_action: `read_existing_snapshot`
- qit_graph_sha256: `82ad2bda2f3be37b7c69cf2d436477fb3a8f40d755e170c076dc2a12885dedda`
- qit_graph_content_hash: `7d25ff22e49d8606ddb8e5dd8e3ee4b6b1cce934fe7da51cd1ad36cc75a768ff`
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
- coarse promotion-gate state for owner structure, cross-layer alignment, runtime state, and history graph presence
- does_not_verify:
- that the owner graph matches docs or runtime semantics beyond the stored snapshot
- that the existing GraphML snapshot is fresh unless it was explicitly refreshed in this run
- that a present runtime evidence bridge constitutes a promoted runtime-state or history graph
- that a present retrieval sidecar constitutes embedding-backed LightRAG retrieval or owner-authoritative memory
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
- LightRAG status: `sidecar_corpus_ready_needs_embedding_config`

## Runtime Evidence Bridge
- status: `present`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md`
- owner_content_hash_matches_current_snapshot: `True`
- runtime_sample_count: `2`
- sim_packet_count: `5`
- complete_mappings: `4`
- partial_mappings: `1`

## Retrieval Sidecar
- status: `present`
- json_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RETRIEVAL_SIDECAR__CURRENT__v1.json`
- md_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RETRIEVAL_SIDECAR__CURRENT__v1.md`
- mode: `lexical_fallback_only`
- retrieval_role: `context_only_non_authoritative`
- allow_owner_writes: `False`
- allow_proof_claims: `False`
- embedding_backed_query: `False`
- document_count: `21`
- top_hit_count: `8`

## Next Actions
- keep owner verification read-only by default and use refresh flags only for intentional artifact regeneration
- treat snapshot_id plus file hashes as the join key for future audit/report surfaces
- admit explicit QIT bridge links through the registry before claiming nested-graph integration beyond summary-level presence
- persist and expand the read-only runtime evidence bridge before promoting runtime/history semantics inward
- use the bounded retrieval sidecar as context only until embedding-backed LightRAG query is configured and explicitly kept non-authoritative
- promote torus/chirality/runtime semantics only after negative-proof and round-trip gates are satisfied
