# QIT Graph Stack Status

- status: `precheck_blocked`
- generated_utc: `2026-03-26T22:36:52Z`
- purpose: `read-only-by-default verification surface over the current QIT owner snapshot and bounded sidecars`
- snapshot_id: `3aaa98dfb9ac8168636856ef68daf67872bd9014ae0132d0bd79532caaee7053`
- git_sha: `ee4f6c20a0da88c8a39ffef56979b3ea42e33aa9`
- owner_builder_sha256: `93e134bbbc9ba32399273c7d8a2d11a57a10f2492697f9a86f36310d24d6997a`

## Owner Layer
- qit_graph_json: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.json`
- qit_graph_action: `read_existing_snapshot`
- qit_graph_sha256: `1a84ab74f23d146e0a2e1ac5ce3396f15d06584cc3f347579b0b2ed5e639c430`
- qit_graph_content_hash: `29a9456b6aa4c15f66d1c7955bd672fe0aba81cb44d6fc1400b4c60114e9fa1b`
- qit_graph_content_hash_matches_recomputed: `True`
- graphml_export: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.graphml`
- graphml_action: `read_existing_snapshot`
- graphml_sha256: `0158f9197931ebf7f6e2938b37ace7a4fb7eae81924d406487ef6faab6125373`
- node_count: `105`
- edge_count: `297`
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
- LightRAG status: `corpus_manifest_ready_init_failed`

## Next Actions
- keep owner verification read-only by default and use refresh flags only for intentional artifact regeneration
- treat snapshot_id plus file hashes as the join key for future audit/report surfaces
- admit explicit QIT bridge links through the registry before claiming nested-graph integration beyond summary-level presence
- materialize runtime-state and history graph surfaces before promoting QIT runtime semantics inward
- complete a bounded embedding-backed query path over the existing LightRAG sidecar corpus, not as owner memory
- promote torus/chirality/runtime semantics only after negative-proof and round-trip gates are satisfied
