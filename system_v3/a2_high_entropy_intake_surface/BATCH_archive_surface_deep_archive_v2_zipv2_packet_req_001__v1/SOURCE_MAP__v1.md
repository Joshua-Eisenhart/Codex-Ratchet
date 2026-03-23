# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
Extraction mode: `ARCHIVE_DEEP_V2_ZIPV2_PACKET_REQ_001_PASS`
Batch scope: archive-only intake of `V2_ZIPV2_PACKET_REQ_001`, bounded to its zero-work run-core files, empty inbox, and single outbound `A0_TO_A1_SAVE_ZIP`
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001`
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
- reason for bounded family batch:
  - this pass processes only `V2_ZIPV2_PACKET_REQ_001` and does not reopen sibling `V2_ZIPV2_REPLAY_001`
  - the archive value is a compact request-only ZIPv2 bootstrap with no accepted work, no retained inbound A1 packet, and one outbound save request carrying a generic sample strategy scaffold
  - this object is useful for demotion lineage because it preserves packet-mode request posture, inert lexical state retention, runtime-path leakage inside archived events, and a split between the outer run state hash and the embedded base-strategy zero-hash scaffold
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001`
- source class: request-only ZIPv2 run root
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id V2_ZIPV2_PACKET_REQ_001`
  - `a1_source packet`
  - `needs_real_llm false`
  - `steps_completed 1`
  - `steps_requested 3`
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
  - promotion counts by tier:
    - none retained

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/state.json`
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
  - retained metadata shells remain populated:
    - `derived_only_terms`
    - `formula_glyph_requirements`
    - `l0_lexeme_set`
  - retained runtime ids are blank:
    - `active_megaboot_id`
    - `active_megaboot_sha256`
    - `active_ruleset_sha256`
- archive meaning:
  - no earned lower-loop state change survives; the retained state is a lexical/bootstrap shell paired with an outbound request posture

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/events.jsonl`
- source class: outbound request ledger
- event markers:
  - retained line count: `1`
  - only event family:
    - `a1_strategy_request_emitted`
  - retained row markers:
    - `step 1`
    - `state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
    - `source ZIP_PROTOCOL_v2`
    - `last_reject_tags []`
  - retained outbound save zip path points to active runtime, not archive mirror:
    - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/runs/V2_ZIPV2_PACKET_REQ_001/zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- archive meaning:
  - the event ledger preserves only an external handoff request and no executed lower-loop work

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/soak_report.md`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/a1_inbox/`
- source class: empty inbound inbox
- retained contents:
  - none
- archive meaning:
  - the run stops after emitting an A0-to-A1 request; no returned A1 strategy packet survives locally

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/zip_packets/`
- source class: outbound save-only packet lattice
- packet file count: `1`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP 1`
- archive meaning:
  - the packet surface preserves only an external-handoff save packet, with no inbound or downstream execution packets

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001/zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- source class: outbound save packet
- sha256: `6563e5f3a71693114f583e98a49e616d7147e672e30fc9336d03e145a71704da`
- size bytes: `1875`
- member hashes:
  - `A0_SAVE_SUMMARY.json 0f5503d8c0481d794c4e858a4a83b825e2ff0c142664b869170db72ecd4b712b`
  - `MANIFEST.json a9c20f18b6066e6e6c7bcf0c3d9be5a8f4c7c9bc6206bb3ad018f165f4d4fa2a`
- packet header markers:
  - `zip_protocol ZIP_PROTOCOL_v2`
  - `zip_type A0_TO_A1_SAVE_ZIP`
  - `direction BACKWARD`
  - `sequence 1`
  - `source_layer A0`
  - `target_layer A1`
  - `run_id V2_ZIPV2_PACKET_REQ_001`
- payload markers:
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
    - placeholder self-audit digests `3333...` and `4444...`
- archive meaning:
  - the only packet is a generic save bootstrap carrying a sample strategy scaffold rather than earned run output
