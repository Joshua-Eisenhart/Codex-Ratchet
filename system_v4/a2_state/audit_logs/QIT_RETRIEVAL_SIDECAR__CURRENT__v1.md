# QIT Retrieval Sidecar

- generated_utc: `2026-03-27T00:12:50Z`
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- owner_graph_role: `read_only_reference_only`
- mode: `lexical_fallback_only`
- retrieval_role: `context_only_non_authoritative`
- allow_owner_writes: `False`
- allow_proof_claims: `False`
- embedding_backed_query: `False`
- embedding_backed_query_blocker: `LightRAG embedding_func not configured`
- query: `type1 type2 chirality coupling`
- corpus_manifest_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/qit_retrieval_sidecar/corpus_manifest.json`
- document_count: `28`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace retrieval-sidecar state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `d2c98a9ee0b15cda05c2eb881adee4848195747a`

## Top Hits
- `qit_hopf_weyl_projection_structured` (audit_reports, score=1.6609, precision_bonus=0.5): ...ery_anchors: hopf, weyl, torus, chirality, clifford, inner, outer, fiber, base, type1, type2 schema: QIT_HOPF_WEYL_PROJECTION_v1 status: present_bounded_projection audit_only: True nonoperative: True do_not_promote: True owner_content_hash:... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.json`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`, `7d25ff22e49d8606ddb8e5dd8e3ee4b6b1cce934fe7da51cd1ad36cc75a768ff`
- `qit_hopf_weyl_projection__current__v1` (audit_reports, score=1.5109, precision_bonus=0.35): ...hash_matches_runtime_bridge: `True` - runtime_sample_count: `2` - `qit::ENGINE::type1_deductive`: first_step=`qit::SUBCYCLE_STEP::type1_deductive_Se_f_Ti`, last_step=`qit::SUBCYCLE_STEP::type1_deductive_Ni_b_Fi` - `qit::ENGINE::type2_induct... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.md`
- `hopf_runtime_alignment__type1_deductive` (audit_reports, score=1.4686, precision_bonus=0.58): # Hopf/Weyl Runtime Alignment: qit::ENGINE::type1_deductive source_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json query_anchors: hopf weyl chirality runtime bridge... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`, `qit::ENGINE::type1_deductive`, `qit::SUBCYCLE_STEP::type1_deductive_Se_f_Ti`, `qit::SUBCYCLE_STEP::type1_deductive_Ni_b_Fi`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`
- `hopf_runtime_alignment__type2_inductive` (audit_reports, score=1.4686, precision_bonus=0.58): ..._PROJECTION__CURRENT__v1.json query_anchors: hopf weyl chirality runtime bridge type1 type2 engine torus engine_public_id: qit::ENGINE::type2_inductive first_step_public_id: qit::SUBCYCLE_STEP::type2_inductive_Se_f_Ti last_step_public_id: q... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`, `qit::ENGINE::type2_inductive`, `qit::SUBCYCLE_STEP::type2_inductive_Se_f_Ti`, `qit::SUBCYCLE_STEP::type2_inductive_Ni_b_Fi`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`
- `hopf_carrier__clifford` (audit_reports, score=1.3986, precision_bonus=0.51): ...label: clifford nesting_rank: 1 stage_count: 16 engine_public_ids: qit::ENGINE::type1_deductive, qit::ENGINE::type2_inductive stage_public_ids: qit::MACRO_STAGE::type1_deductive_Ne_b, qit::MACRO_STAGE::type1_deductive_Ne_f, qit::MACRO_STAGE... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`, `qit::TORUS::clifford`, `qit::MACRO_STAGE::type1_deductive_Ne_b`, `qit::MACRO_STAGE::type1_deductive_Ne_f`, `qit::MACRO_STAGE::type1_deductive_Ni_b`
- `hopf_carrier__inner` (audit_reports, score=1.3986, precision_bonus=0.51): ...ner label: inner nesting_rank: 0 stage_count: 8 engine_public_ids: qit::ENGINE::type1_deductive, qit::ENGINE::type2_inductive stage_public_ids: qit::MACRO_STAGE::type1_deductive_Ne_f, qit::MACRO_STAGE::type1_deductive_Ni_f, qit::MACRO_STAGE... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`, `qit::TORUS::inner`, `qit::MACRO_STAGE::type1_deductive_Ne_f`, `qit::MACRO_STAGE::type1_deductive_Ni_f`, `qit::MACRO_STAGE::type1_deductive_Se_f`
- `hopf_carrier__outer` (audit_reports, score=1.3986, precision_bonus=0.51): ...ter label: outer nesting_rank: 2 stage_count: 8 engine_public_ids: qit::ENGINE::type1_deductive, qit::ENGINE::type2_inductive stage_public_ids: qit::MACRO_STAGE::type1_deductive_Ne_b, qit::MACRO_STAGE::type1_deductive_Ni_b, qit::MACRO_STAGE... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json`, `qit::TORUS::outer`, `qit::MACRO_STAGE::type1_deductive_Ne_b`, `qit::MACRO_STAGE::type1_deductive_Ni_b`, `qit::MACRO_STAGE::type1_deductive_Se_b`
- `qit_graph_layer_mapping` (qit_docs, score=1.1609, precision_bonus=0.0): ...ayer | What It Holds | Status | |---|---|---| | **NetworkX (owner)** | `ENGINE::type1_deductive`, `ENGINE::type2_inductive` nodes + `CHIRALITY_COUPLING` edge + `ENGINE_OWNS_STAGE` edges (16 per type) | **Live.** Structural facts. | | **clif... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/QIT_GRAPH_LAYER_MAPPING.md`

## Boundary
- This retrieval surface is sidecar-only and non-authoritative.
- It may read graph-adjacent docs and evidence, but it does not write owner truth.
- Retrieved text is context, not proof.
- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.