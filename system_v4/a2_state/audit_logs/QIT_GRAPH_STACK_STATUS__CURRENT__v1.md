# QIT Graph Stack Status

- status: `precheck_blocked`
- generated_utc: `2026-03-26T22:58:28Z`
- purpose: `read-only-by-default verification surface over the current QIT owner snapshot and bounded sidecars`
- snapshot_id: `e21502aa1545dfd7e0c0ed3c0f7f081b12f631c23dce026108893e582bf622f4`
- git_sha: `f5c317d544b67c27521c7d53810946d7594486de`
- owner_builder_sha256: `9bd0a8faa9e99db5174496039a53026663e3f8706d66d2e5d4d216882d84099a`

## Owner Layer
- qit_graph_json: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.json`
- qit_graph_action: `read_existing_snapshot`
- qit_graph_sha256: `3d47ff0839cfc8af4cbd7c40ce5b85fbeff6a9c91aaa4f9f9a9323c340e8ab72`
- qit_graph_content_hash: `019ace7d8072508e1e1e3bc3931e36155be38652255e1f55993a47fc053406ee`
- qit_graph_content_hash_matches_recomputed: `True`
- graphml_export: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.graphml`
- graphml_action: `read_existing_snapshot`
- graphml_sha256: `0158f9197931ebf7f6e2938b37ace7a4fb7eae81924d406487ef6faab6125373`
- node_count: `105`
- edge_count: `282`
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
- coarse promotion-gate state for owner structure, cross-layer alignment, runtime state, and history graph presence
- does_not_verify:
- that the owner graph matches docs or runtime semantics beyond the stored snapshot
- that the existing GraphML snapshot is fresh unless it was explicitly refreshed in this run
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

## Next Actions
- keep owner verification read-only by default and use refresh flags only for intentional artifact regeneration
- treat snapshot_id plus file hashes as the join key for future audit/report surfaces
- admit explicit QIT bridge links through the registry before claiming nested-graph integration beyond summary-level presence
- materialize runtime-state and history graph surfaces before promoting QIT runtime semantics inward
- complete a bounded embedding-backed query path over the existing LightRAG sidecar corpus, not as owner memory
- promote torus/chirality/runtime semantics only after negative-proof and round-trip gates are satisfied
