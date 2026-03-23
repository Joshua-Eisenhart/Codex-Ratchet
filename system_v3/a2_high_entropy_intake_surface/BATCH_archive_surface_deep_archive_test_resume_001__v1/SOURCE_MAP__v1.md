# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_resume_001__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_RESUME_001_PASS`
Batch scope: archive-only intake of `TEST_RESUME_001`, bounded to its zero-work run-core files, empty inbox residue, missing sequence ledger, duplicate A0-to-A1 save exports, and embedded save-summary payloads
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001`
  - retained run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `soak_report.md`
  - retained directories:
    - `a1_inbox/`
    - `zip_packets/`
  - packet family under `zip_packets/`:
    - `000001_A0_TO_A1_SAVE_ZIP.zip`
    - `000002_A0_TO_A1_SAVE_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `TEST_RESUME_001` and does not reopen sibling `TEST_STATE_TRANSITION_CHAIN_A`
  - the archive value is a compact external-handoff stub with no accepted work, no inbound A1 strategy, two emitted save requests, and a duplicated save payload
  - this object is useful for demotion lineage because it preserves packet-outbound resume behavior, active-runtime path leakage inside archived events, sample-strategy placeholder residue, and duplicated step-1 request emission without any earned lower-loop state change
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001`
- source class: zero-work resume/request run root
- retained top-level contents:
  - `a1_inbox/`
  - `events.jsonl`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets/`
- missing top-level runtime surface:
  - `sequence_state.json` not retained

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id TEST_RESUME_001`
  - `a1_source packet`
  - `needs_real_llm false`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 0`
  - `unresolved_promotion_blocker_count 0`
  - `stop_reason A1_NEEDS_EXTERNAL_STRATEGY`
  - retained digest diversity:
    - `unique_strategy_digest_count 0`
    - `unique_export_content_digest_count 0`
    - `unique_export_structural_digest_count 0`
  - `final_state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/state.json`
- source class: retained inert final state
- compact state markers:
  - `accepted_batch_count 0`
  - `canonical_ledger_len 0`
  - `evidence_tokens_len 0`
  - `probe_meta_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 0`
  - `sim_registry_len 0`
  - `sim_results_len 0`
  - `survivor_ledger_len 0`
  - `evidence_pending_len 0`
  - `kill_log_len 0`
  - retained metadata shells:
    - `derived_only_terms` populated
    - `formula_glyph_requirements` populated
    - `l0_lexeme_set` populated
  - retained runtime ids:
    - `active_megaboot_id` empty
    - `active_megaboot_sha256` empty
    - `active_ruleset_sha256` empty
- archive meaning:
  - no earned state change survives; the run preserves only a clean lexical shell plus an outbound request posture

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/events.jsonl`
- source class: outbound event ledger
- event markers:
  - retained line count: `2`
  - only event family:
    - `a1_strategy_request_emitted`
  - both retained rows keep:
    - `step 1`
    - `state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
    - `source ZIP_PROTOCOL_v2`
    - `last_reject_tags []`
  - retained outbound save zip paths point to active runtime, not archive mirror:
    - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/runs/TEST_RESUME_001/zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
    - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/runs/TEST_RESUME_001/zip_packets/000002_A0_TO_A1_SAVE_ZIP.zip`
- archive meaning:
  - the event ledger preserves duplicated outbound request emission rather than executed lower-loop work

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason A1_NEEDS_EXTERNAL_STRATEGY`
  - top failure tags:
    - `NONE`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/a1_inbox/`
- source class: empty inbound inbox
- retained contents:
  - none
- archive meaning:
  - the run stops after emitting A0-to-A1 requests; no returned A1 strategy packet survives locally

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/zip_packets/`
- source class: outbound save-only packet lattice
- packet file count: `2`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP 2`
- archive meaning:
  - the packet surface preserves only external-handoff save packets, with no inbound or downstream execution packets

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- source class: first outbound save packet
- sha256: `c7255dcd2adc0e17f2c4126bceab12360335301c63e95b3d2bec5b4429973fb0`
- size bytes: `1867`
- member hashes:
  - `A0_SAVE_SUMMARY.json 1975a9faa65bb61d07f70ac882f670df7643a632e6e02b88224fefbbea7753e6`
  - `MANIFEST.json 54c1b19add21f6568eb56b39306e5d7a9107b964a090c16a0d12f3b002d78023`
  - `ZIP_HEADER.json acc84c0e01b866aae05b4c6035033b924eefd9c1480caa3c1aa6b1381d1a3945`
- payload markers:
  - `zip_protocol ZIP_PROTOCOL_v2`
  - `sequence 1`
  - `run_id TEST_RESUME_001`
  - `A0_SAVE_SUMMARY.schema A0_SAVE_SUMMARY_v1`
  - top-level save summary:
    - `step 1`
    - `state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
    - `last_reject_tags []`
  - embedded base strategy:
    - `strategy_id STRAT_SAMPLE_0001`
    - target `S_BIND_ALPHA`
    - alternative `S_BIND_ALPHA_ALT`
    - positive sim `SIM_POS_BIND_ALPHA`
    - negative sim `SIM_NEG_BIND_ALPHA`
    - target family `BASELINE`
    - alternative family `ADVERSARIAL_NEG`
    - target tier `T0_ATOM`
    - alternative tier `T0_ATOM`
    - `inputs.state_hash` all zeroes
    - placeholder self-audit hashes `2222...`, `3333...`, `4444...`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001/zip_packets/000002_A0_TO_A1_SAVE_ZIP.zip`
- source class: second outbound save packet
- sha256: `5ec172c9dfe7200a478d52071064d5774f4ba1da80acb8a582e4a5c61bf0398b`
- size bytes: `1866`
- member hashes:
  - `A0_SAVE_SUMMARY.json 1975a9faa65bb61d07f70ac882f670df7643a632e6e02b88224fefbbea7753e6`
  - `MANIFEST.json 54c1b19add21f6568eb56b39306e5d7a9107b964a090c16a0d12f3b002d78023`
  - `ZIP_HEADER.json 0a41ef56a1591c0a4b9eb99c5b8861bfced4b70c26b56d0986bf75cb25a2eb33`
- payload markers:
  - `zip_protocol ZIP_PROTOCOL_v2`
  - `sequence 2`
  - `run_id TEST_RESUME_001`
  - identical save-summary payload to sequence `1`
  - top-level save summary still reports:
    - `step 1`
    - `state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
    - `last_reject_tags []`
- archive meaning:
  - the second packet preserves duplicated outbound handoff using the same payload with only the header sequence updated
