# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_PACKET_EMPTY_PASS`
Batch scope: archive-only intake of `TEST_A1_PACKET_EMPTY`, bounded to its run-root files, empty inbox residue, lone A0 save packet, and duplicate empty `zip_packets 2` packaging residue
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY`
  - retained run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
  - retained directories:
    - `a1_inbox/`
    - `zip_packets/`
    - `zip_packets 2/`
  - packet surface:
    - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
    - embedded `MANIFEST.json`
    - embedded `ZIP_HEADER.json`
    - embedded `A0_SAVE_SUMMARY.json`
- reason for bounded family batch:
  - this pass processes only `TEST_A1_PACKET_EMPTY` and does not reopen sibling `TEST_*` or `V2_*` runs
  - the archive value is not runtime progress but boundary failure texture: the run stops before any A1 response arrives, yet the saved A0 packet still carries a nonempty strategy skeleton
  - this object is useful as demotion lineage for the A0-to-A1 handoff boundary because all visible run-core surfaces align cleanly on a one-step zero-acceptance state while the saved packet implies intended downstream work that never occurred
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_ZIP`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY`
- source class: minimal archived run root
- retained top-level contents:
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
  - `sequence_state.json`
  - `soak_report.md`
  - `a1_inbox/`
  - `zip_packets/`
  - `zip_packets 2/`
- archive meaning:
  - this is a thin handoff-failure run root, not a substantive multi-step execution

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id TEST_A1_PACKET_EMPTY`
  - `a1_model` empty
  - `a1_source packet`
  - `steps_completed 1`
  - `steps_requested 3`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 0`
  - `unresolved_promotion_blocker_count 0`
  - `stop_reason A1_NEEDS_EXTERNAL_STRATEGY`
  - `unique_strategy_digest_count 0`
  - `unique_export_content_digest_count 0`
  - `unique_export_structural_digest_count 0`
  - `final_state_hash 7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/state.json`
- source class: final run state
- compact state markers:
  - `accepted_batch_count 0`
  - `derived_only_terms_len 47`
  - `l0_lexeme_set_len 19`
  - `canonical_ledger_len 0`
  - `evidence_pending_len 0`
  - `evidence_tokens_len 0`
  - `interaction_counts_len 0`
  - `kill_log_len 0`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 0`
  - `sim_registry_len 0`
  - `sim_results_len 0`
  - `term_registry_len 0`
  - `probe_meta_len 0`
  - `spec_meta_len 0`
  - `survivor_ledger_len 2`
  - `survivor_order_len 2`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained seed surfaces:
  - survivor ids:
    - `F01_FINITUDE`
    - `N01_NONCOMMUTATION`
  - lexical seed families remain preloaded while execution-facing registries remain empty

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/sequence_state.json`
- source class: global sequence ledger
- sequence maxima:
  - `A0 1`
  - `A1 0`
  - `A2 0`
  - `B 0`
  - `SIM 0`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/events.jsonl`
- source class: single-event ledger
- event markers:
  - retained line count: `1`
  - only event:
    - `a1_strategy_request_emitted`
  - event step: `1`
  - source: `ZIP_PROTOCOL_v2`
  - linked packet path points back to the runtime-root `000001_A0_TO_A1_SAVE_ZIP.zip`
  - event `state_hash` matches summary/state final hash

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason A1_NEEDS_EXTERNAL_STRATEGY`
  - top failure tags:
    - `NONE`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/a1_inbox/`
- source class: empty inbox residue
- retained contents:
  - none
- archive meaning:
  - the request for an A1 strategy survives, but no A1 packet or consumed residue does

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- source class: lone backward save packet
- sha256: `6884b5a853fecf5dd34dd83b06f3146f257e695db3f946cd862741945bac0fa7`
- size bytes: `1876`
- zip members:
  - `HASHES.sha256`
  - `MANIFEST.json`
  - `ZIP_HEADER.json`
  - `A0_SAVE_SUMMARY.json`
- packet header markers:
  - `zip_type A0_TO_A1_SAVE_ZIP`
  - `direction BACKWARD`
  - `source_layer A0`
  - `target_layer A1`
  - `sequence 1`
  - `zip_protocol ZIP_PROTOCOL_v2`
  - `created_utc 1980-01-01T00:00:00Z`
- packet manifest markers:
  - only hashed payload entry:
    - `A0_SAVE_SUMMARY.json`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- zip member path: `A0_SAVE_SUMMARY.json`
- source class: saved A0 handoff payload
- payload markers:
  - `schema A0_SAVE_SUMMARY_v1`
  - `run_id TEST_A1_PACKET_EMPTY`
  - `step 1`
  - `state_hash 7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`
  - `strategy_id STRAT_SAMPLE_0001`
  - `budget max_items 3`
  - `budget max_sims 3`
  - targets:
    - base target `S_BIND_ALPHA`
  - negative alternatives:
    - `S_BIND_ALPHA_ALT`
  - operator ids used:
    - `OP_BIND_SIM`
    - `OP_NEG_SIM_EXPAND`
  - placeholder-bound input hashes:
    - bootpack rules hash of repeated `2`
    - fuel slice hash of repeated `1`
    - strategy hash of repeated `3`
    - compile lane digest of repeated `4`
- archive meaning:
  - the handoff packet contains a concrete but obviously placeholder-heavy strategy skeleton even though the run never ingests an external A1 strategy

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY/zip_packets 2/`
- source class: duplicate empty packaging residue
- retained contents:
  - none
- permissions note:
  - directory mode is more restrictive than the neighboring retained directories
- archive meaning:
  - preserved as packaging noise only; not a live packet lane
