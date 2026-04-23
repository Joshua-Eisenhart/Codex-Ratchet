# QIT Runtime Evidence Bridge

- generated_utc: `2026-03-30T10:46:52Z`
- audit_only: `True`
- nonoperative: `True`
- do_not_promote: `True`
- persistence_policy: `persisted_audit_log_packet`
- owner_graph_role: `read_only_reference_only`
- runtime_capture_mode: `deterministic_sample_replay`
- live_runtime_capture: `False`
- owner_content_hash: `585499a4d13298615601af806cf9c0d01f56ef6e47879c5c82abf39227ef373a`

## Report Surface
- surface_class: `tracked_current_workspace_report`
- represents: `current workspace runtime/evidence bridge state at generation time; may differ from the last committed snapshot until tracked CURRENT artifacts are committed`
- git_sha: `56e79ea13dac0552c8ec43f6fa7da2e55c764e44`

## Axis0 Control-Plane Summary
- surface_status: `read_only_control_plane_summary_only`
- runtime_sample_count: `2`
- direct_bridge_families: `Xi_LR_direct_control`
- history_window_bridge_families: `Xi_hist_window_control`
- history_window_sample_counts: `32`

## Runtime Samples
- qit::ENGINE::type1_left_weyl: `32` steps, last step `qit::SUBCYCLE_STEP::type1_left_weyl_Ne_f_Fi`, `axis0_bridge_snapshot` `Xi_LR_direct_control`, `axis0_history_window_snapshot` `Xi_hist_window_control` (32 samples)
- qit::ENGINE::type2_right_weyl: `32` steps, last step `qit::SUBCYCLE_STEP::type2_right_weyl_Si_b_Fi`, `axis0_bridge_snapshot` `Xi_LR_direct_control`, `axis0_history_window_snapshot` `Xi_hist_window_control` (32 samples)

## SIM Evidence Packets
- neg_axis6_shared_stage_matrix_results.json: `complete` (resolved_links=2, unresolved_links=0)
- neg_missing_fe_stage_matrix_results.json: `complete` (resolved_links=2, unresolved_links=0)
- neg_missing_operator_stage_matrix_results.json: `complete` (resolved_links=5, unresolved_links=0)
- neg_native_only_stage_matrix_results.json: `witness_only` (resolved_links=1, unresolved_links=0)
- neg_type_flatten_stage_matrix_results.json: `partial` (resolved_links=1, unresolved_links=2)

## Summary
- runtime_sample_count: `2`
- sim_packet_count: `5`
- complete_mappings: `3`
- partial_mappings: `2`
- missing_packets: `0`
- resolved_owner_links: `11`
- unresolved_owner_links: `2`

## Boundary
- This is a read-only audit-log packet/report surface.
- It is not a promoted runtime-state graph.
- It is not a promoted history graph.
- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.