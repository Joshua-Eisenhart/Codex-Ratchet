# EXPLICIT_NAME_ALIAS_SURFACE_v1

Purpose:
- Provide long, explicit directory names without breaking existing runtime/tool paths.
- Keep short names as compatibility aliases during migration.

Policy:
- Long explicit aliases are the operator-facing names.
- Short names remain compatibility paths until all tooling is fully migrated.
- No behavioral/runtime semantics are changed by this file.

Top-level `system_v3/` alias mapping:
- `a2_derived_indices_noncanonical` -> `a2_noncanonical_derived_index_cache_surface`
- `a2_state` -> `a2_persistent_context_and_memory_surface`
- `conformance` -> `conformance_and_fixture_validation_surface`
- `control_plane_bundle_work` -> `control_plane_bundle_authoring_workspace_surface`
- `public_facing_docs` -> `public_facing_documentation_surface`
- `runs` -> `deterministic_campaign_run_surface`
- `runtime` -> `deterministic_runtime_execution_surface`
- `specs` -> `noncanonical_draft_specification_surface`
- `tools` -> `deterministic_operational_tooling_surface`

Run-surface alias mapping (`system_v3/runs/<RUN_ID>/`):
- `a1_inbox` -> `a1_packet_inbox_surface`
- `a1_strategies` -> `optional_a1_strategy_duplicate_surface`
- `outbox` -> `deterministic_outbound_export_block_cache_surface`
- `reports` -> `deterministic_compile_and_kernel_report_surface`
- `sim` -> `optional_plaintext_sim_evidence_duplicate_surface`
- `snapshots` -> `optional_plaintext_snapshot_duplicate_surface`
- `zip_packets` -> `zip_protocol_v2_packet_journal_surface`

Migration mode:
- Current mode is `compatibility_alias_mode = ON`.
- Hard-cut removal of short names is deferred until all tools/tests reference explicit paths.
