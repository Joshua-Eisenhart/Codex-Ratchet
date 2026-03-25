# CONTROLLER_COLD_INDEX__v1
Status: PROPOSED / NONCANONICAL / CONTROLLER COLD INDEX
Date: 2026-03-16
Role: bounded cold-index listing for intake batches whose ledger status is exactly `REVISIT_REQUIRED`

## Scope
- derived in one bounded pass from `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- application rule source: `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/parallel_codex_worker_returns/A2_WORKER__A2_INTAKE_COLD_INDEX_APPLICATION_PLAN__2026_03_16__v1__return.txt`
- keyed only by existing batch id and current status
- later re-warming requires an explicit bounded nomination naming exact batch ids

## Cold gate
- include only batches whose ledger status is exactly `REVISIT_REQUIRED`
- keep these out of default controller-visible warm review sets
- do not convert these entries into blocked or promotable state by this surface
- exclude all `A2_2_CANDIDATE` batches from this cold index
- exclude all `BATCH_A2MID_*` batches from this cold index
- exclude blocked integrity-residue classes from this cold index

## Cold listing
- `BATCH_a2feed_leviathan_family_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_a2feed_grok_gemini_digested_model_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_a2feed_grok_unified_physics_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_a2feed_grok_unified_phuysics_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_upgrade_docs_bootpack_thread_a_engine_pattern__v1` - `REVISIT_REQUIRED`
- `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1` - `REVISIT_REQUIRED`
- `BATCH_upgrade_docs_megaboot_ratchet_suite_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_axis_foundation_companion_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_axes_order_trigrams_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_axis12_topology_math_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_axis3_hopf_loops_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_axis4_qit_math_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_axis4_vs_axis5_heat_cold_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_constraints_entropy_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_constraints_source_map__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_constraints_entropy_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_refinedfuel_constraints_term_conflict__v1` - `REVISIT_REQUIRED`
- `BATCH_upgrade_docs_jp_graph_prompt_engine_pattern__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch02_axes_apple_notes_igt_mapping__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch04_leviathan_model_interpretation_cluster__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch05_thread_b_trigram_and_megaboot__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch06_upgrade_bootpack_and_plan_passes_1_4__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch07_upgrade_plan_passes_5_9_and_directed_audit__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch08_runtime_archive_structural_memory__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch09_sim_protocol_and_evidence_surface__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_batch10_thread_s_full_save_kit_vocabulary_surface__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_root_milestone_split__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_migrated_run_root_registry_and_family_signatures__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_foundation_batch_0001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle_v2__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_bundle__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_foundation_ladder_001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_hardmode_clean_0001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0002__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0003__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0004__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0005__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_registry_smoke_0001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_semantic_sim_0001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_signal_0002__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_signal_0003__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_signal_0004__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_signal_0005__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_det_a__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_det_b__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_real_a1_001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_real_a1_002__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_resume_001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_heat_dumps_root_family_split__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_heat_dumps_20260225T070252Z_root_split__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_heat_dumps_run_engine_entropy_0001__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_heat_dumps_repo_archive_moved_out_of_git__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_heat_dumps_nested_cache_recent_purgeable__v1` - `REVISIT_REQUIRED`
- `BATCH_archive_surface_heat_dumps_nested_heat_dump_hub__v1` - `REVISIT_REQUIRED`

## Count
- total listed cold entries: `69`

## Admission note
- surface class for this bounded execution artifact: `RUNTIME_ONLY`
- this file does not mutate ledger status, owner-surface authority, or intake taxonomy
