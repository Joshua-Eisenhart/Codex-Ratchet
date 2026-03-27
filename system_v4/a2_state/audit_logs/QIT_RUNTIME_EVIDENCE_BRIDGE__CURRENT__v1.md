# QIT Runtime Evidence Bridge

- generated_utc: `2026-03-27T00:04:05Z`
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- persistence_policy: `persisted_audit_log_packet`
- owner_graph_role: `read_only_reference_only`
- runtime_capture_mode: `deterministic_sample_replay`
- live_runtime_capture: `False`
- owner_content_hash: `7d25ff22e49d8606ddb8e5dd8e3ee4b6b1cce934fe7da51cd1ad36cc75a768ff`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace runtime/evidence bridge state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `ba04c7bf2dce21142fd3289b7c2ada1a5453dde6`

## Runtime Samples
- qit::ENGINE::type1_deductive: `32` steps, last step `qit::SUBCYCLE_STEP::type1_deductive_Ni_b_Fi`
- qit::ENGINE::type2_inductive: `32` steps, last step `qit::SUBCYCLE_STEP::type2_inductive_Ni_b_Fi`

## SIM Evidence Packets
- neg_axis6_shared_stage_matrix_results.json: `complete` (resolved_links=2, unresolved_links=0)
- neg_missing_fe_stage_matrix_results.json: `complete` (resolved_links=2, unresolved_links=0)
- neg_missing_operator_stage_matrix_results.json: `complete` (resolved_links=5, unresolved_links=0)
- neg_native_only_stage_matrix_results.json: `witness_only` (resolved_links=1, unresolved_links=0)
- neg_type_flatten_stage_matrix_results.json: `complete` (resolved_links=3, unresolved_links=0)

## Summary
- runtime_sample_count: `2`
- sim_packet_count: `5`
- complete_mappings: `4`
- partial_mappings: `1`
- missing_packets: `0`
- resolved_owner_links: `13`
- unresolved_owner_links: `0`

## Boundary
- This is a read-only audit-log packet/report surface.
- It is not a promoted runtime-state graph.
- It is not a promoted history graph.
- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.