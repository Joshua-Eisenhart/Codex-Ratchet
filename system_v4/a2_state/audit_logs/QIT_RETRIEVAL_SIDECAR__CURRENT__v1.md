# QIT Retrieval Sidecar

- generated_utc: `2026-03-27T00:17:25Z`
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
- query: `Which QIT runtime evidence surfaces are live now, and how do axis 6, missing Fe, and type flatten negatives map into the current graph lane?`
- corpus_manifest_path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/qit_retrieval_sidecar/corpus_manifest.json`
- document_count: `30`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace retrieval-sidecar state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `7391077305b05a3e82e5cf38aaf7b42e236f41b3`

## Top Hits
- `qit_graph_sync_readme` (qit_docs, score=1.3441, precision_bonus=0.16): ... |---|---| | `core_docs/QIT_GRAPH_LAYER_MAPPING.md` | Conceptual Rosetta stone: which physics concept lives in which graph layer | | `core_docs/QIT_GRAPH_SCHEMA.md` | Canonical node and edge inventory (7 live node types + 1 schema-ready typ... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/QIT_GRAPH_SYNC_README.md`
- `qit_hopf_weyl_evidence_audit__current__v1` (audit_reports, score=1.3344, precision_bonus=0.29): # Source Document: QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.md source_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.md # QIT Hopf/Weyl Evidence Audit - status: `b... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.md`
- `qit_graph_runtime_model` (qit_docs, score=1.2374, precision_bonus=0.24): ...ate Variable | Type | Description | |---|---|---| | `current_stage` | int 0–7 | Which macro-stage is active | | `current_operator` | int 0–3 | Future finer-grain state field. Not yet surfaced by the current packet-only bridge. | | `current_... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/QIT_GRAPH_RUNTIME_MODEL.md`
- `qit_graph_stack_status__current__v1` (audit_reports, score=1.1923, precision_bonus=0.29): # Source Document: QIT_GRAPH_STACK_STATUS__CURRENT__v1.md source_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.md # QIT Graph Stack Status - status: `precheck_blocked` -... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.md`
- `qit_hopf_weyl_evidence_audit_structured` (audit_reports, score=1.1756, precision_bonus=0.37): ...ath: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.json query_anchors: hopf, weyl, torus, chirality, evidence audit, safe now, missing now, forbidden claims schema: QIT_... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.json`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/qit_engine_graph_v1.json`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`, `7d25ff22e49d8606ddb8e5dd8e3ee4b6b1cce934fe7da51cd1ad36cc75a768ff`, `qit::ENGINE::type1_deductive`
- `qit_runtime_evidence_bridge__current__v1` (audit_reports, score=1.1756, precision_bonus=0.37): # Source Document: QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md source_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md # QIT Runtime Evidence Bridge - generated_utc... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md`
- `runtime_bridge__neg_missing_fe_stage_matrix_results` (runtime_bridge, score=1.1231, precision_bonus=0.57): ...ath: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json result_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/neg_missing_fe_sta... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/neg_missing_fe_stage_matrix_results.json`, `qit::NEG_WITNESS::neg_missing_fe`, `qit::OPERATOR::Fe`
- `runtime_bridge__neg_missing_operator_stage_matrix_results` (runtime_bridge, score=1.1231, precision_bonus=0.57): ...ath: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json result_path: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/neg_missing_operat... | refs: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json`, `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/neg_missing_operator_stage_matrix_results.json`, `qit::NEG_WITNESS::neg_missing_operator`, `qit::OPERATOR::Ti`, `qit::OPERATOR::Fe`

## Boundary
- This retrieval surface is sidecar-only and non-authoritative.
- It may read graph-adjacent docs and evidence, but it does not write owner truth.
- Retrieved text is context, not proof.
- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.