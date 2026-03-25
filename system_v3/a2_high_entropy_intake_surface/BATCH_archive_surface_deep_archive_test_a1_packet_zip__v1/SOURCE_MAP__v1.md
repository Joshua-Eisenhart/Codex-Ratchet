# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_PACKET_ZIP_PASS`
Batch scope: archive-only intake of `TEST_A1_PACKET_ZIP`, bounded to its run-root files, inbox and consumed strategy packet copies, the single-step packet lattice, and embedded packet payloads
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP`
  - retained run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
  - retained packet copies:
    - `a1_inbox/000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `TEST_A1_PACKET_ZIP` and does not reopen sibling `TEST_DET_*` or `TEST_REAL_A1_*` runs
  - the archive value is a tightly bounded single-step packet-loop object with four live packet kinds and three copies of the strategy zip, but deeply contradictory run-state summaries
  - this object is especially useful for demotion lineage because it preserves both a structurally richer transport-lane strategy packet and a schema-invalid inbox copy of the same named packet
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_A`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP`
- source class: one-step packet-loop run root
- retained top-level contents:
  - `a1_inbox/`
  - `events.jsonl`
  - `sequence_state.json`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets/`

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/summary.json`
- source class: terminal summary surface
- summary markers:
  - `run_id TEST_A1_PACKET_ZIP`
  - `a1_model` empty
  - `a1_source packet`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 3`
  - `unresolved_promotion_blocker_count 0`
  - `stop_reason MAX_STEPS`
  - `unique_strategy_digest_count 0`
  - `unique_export_content_digest_count 0`
  - `unique_export_structural_digest_count 0`
  - `final_state_hash aed8327fa78122bdcf8a56ba2beaeeb7becea60b94ab34e11e134231c9642611`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/state.json`
- source class: retained final state
- compact state markers:
  - `accepted_batch_count 2`
  - `canonical_ledger_len 2`
  - canonical ledger steps:
    - `1`
    - `2`
  - canonical ledger sequences:
    - `1`
    - `2`
  - `evidence_tokens_len 2`
  - `kill_log_len 2`
  - `reject_log_len 1`
  - `probe_meta_len 2`
  - `sim_promotion_status_len 3`
  - `sim_registry_len 3`
  - `sim_results_len 2`
  - `spec_meta_len 3`
  - `survivor_ledger_len 7`
  - survivor statuses:
    - `ACTIVE 5`
    - `KILLED 2`
  - kill token counts:
    - `NEG_NEG_BOUNDARY 2`
  - reject markers:
    - `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`
- archive meaning:
  - state retains evidence of two accepted batches and a later schema failure even though the summary reports zero accepted work

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/sequence_state.json`
- source class: global sequence ledger
- sequence maxima:
  - `A0 0`
  - `A1 0`
  - `A2 0`
  - `B 0`
  - `SIM 0`
- archive meaning:
  - this zeroed sequence surface contradicts the visible presence of one packet in every active lane

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/events.jsonl`
- source class: duplicated event ledger
- event markers:
  - retained line count: `32`
  - duplicated success rows:
    - `3` identical `step_result` rows
  - duplicated failure rows:
    - `29` identical `a1_generation_fail` rows
  - success-row totals:
    - `accepted_sum 6`
    - `parked_sum 0`
    - `rejected_sum 0`
    - all success rows at step `1`
    - shared `state_hash_after 3aede158a802eb4069e43580ff85ea5a307e192f39e269b7bf932d3f4a39f4a8`
  - repeated fail error:
    - `a1_packet_schema_fail:alternatives must be non-empty when require_try_to_fail is true;self_audit.candidate_count must equal len(targets)`
- archive meaning:
  - the event lattice preserves both successful execution and repeated fail-closed regeneration noise at the same step

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/soak_report.md`
- source class: human-readable run report
- report markers:
  - `cycle_count 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/a1_inbox/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: inbox strategy packet copy
- sha256: `b912f7b97a89a34964a513afe9ad54a94315fdc58524a470dddcaa58b856ddf0`
- size bytes: `1491`
- content markers:
  - `alternatives` empty
  - `self_audit.alternative_count 0`
  - `self_audit.candidate_count 0`
  - `state_hash` all zeros
- archive meaning:
  - this is the schema-invalid strategy form echoed by the repeated `a1_generation_fail` events

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: consumed strategy packet copy
- sha256: `b912f7b97a89a34964a513afe9ad54a94315fdc58524a470dddcaa58b856ddf0`
- size bytes: `1491`
- relation to inbox packet:
  - byte-identical to the inbox copy

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: transport-lane strategy packet
- sha256: `71b8c1dab70472ada69817b0ad8e05274faaf3c9979c2924863bb93f7ef33b44`
- size bytes: `1935`
- packet header markers:
  - `zip_type A1_TO_A0_STRATEGY_ZIP`
  - `direction FORWARD`
  - `source_layer A1`
  - `target_layer A0`
  - `sequence 1`
- payload markers:
  - `strategy_id STRAT_TEST`
  - one baseline target:
    - `S_BIND_ALPHA_S0001`
  - one negative alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
  - `budget max_items 1`
  - `budget max_sims 1`
  - `self_audit.alternative_count 1`
  - `self_audit.candidate_count 1`
  - `inputs.state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
- archive meaning:
  - this copy is materially richer than the inbox/consumed copy despite sharing the same packet name and sequence

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- source class: export batch packet
- sha256: `4a864c4fdaaaed45ba7bf78c8341ccf117fd844a59d71dabb8f41110c003b119`
- size bytes: `1324`
- packet header markers:
  - `zip_type A0_TO_B_EXPORT_BATCH_ZIP`
  - `direction FORWARD`
  - `source_layer A0`
  - `target_layer B`
  - `sequence 1`
- payload markers:
  - export block proposes:
    - `P_BIND_ALPHA`
    - `S_BIND_ALPHA_S0001`
  - target:
    - `THREAD_B_ENFORCEMENT_KERNEL`

### Source 12
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
- source class: Thread-S snapshot packet
- sha256: `37f7dd8d4ed70d9e6041648e25232692818cf5beb394a624ac9f83c2aab222da`
- size bytes: `1422`
- packet header markers:
  - `zip_type B_TO_A0_STATE_UPDATE_ZIP`
  - `direction BACKWARD`
  - `source_layer B`
  - `target_layer A0`
  - `sequence 1`
- payload markers:
  - snapshot format:
    - `THREAD_S_SAVE_SNAPSHOT v2`
  - provenance:
    - `ACCEPTED_BATCH_COUNT=1`
  - evidence pending:
    - `S_BIND_ALPHA_S0001` requires `E_BIND_ALPHA`

### Source 13
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP/zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- source class: SIM result packet
- sha256: `c2ac995e3e1ac4f0268d5b8935dda1157d8f48c0d1624dc0e1dca1a5c952a1c6`
- size bytes: `1385`
- packet header markers:
  - `zip_type SIM_TO_A0_SIM_RESULT_ZIP`
  - `direction BACKWARD`
  - `source_layer SIM`
  - `target_layer A0`
  - `sequence 1`
- payload markers:
  - `SIM_ID S_BIND_ALPHA_S0001`
  - `tier T1_COMPOUND`
  - `family PERTURBATION`
  - `negative_class NEG_BOUNDARY`
  - evidence signal:
    - `E_BIND_ALPHA`
  - kill signal:
    - `NEG_NEG_BOUNDARY`
