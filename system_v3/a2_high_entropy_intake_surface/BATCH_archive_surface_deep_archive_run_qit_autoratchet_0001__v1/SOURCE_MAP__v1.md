# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_QIT_AUTORATCHET_PASS`
Batch scope: archive-only intake of `RUN_QIT_AUTORATCHET_0001`, bounded to the direct run root, core run-state surfaces, `sequence_state.json`, the embedded packet lattice, and the split active/consumed inbox lanes
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001`
  - core run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
    - `zip_packets/`
  - inbox residue surfaces:
    - `a1_inbox/`
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the direct run `RUN_QIT_AUTORATCHET_0001` and does not reopen sibling runs
  - the archive value is a small autoratchet run that preserves a one-step accepted result, then immediate repeated generation failure and queue backlog
  - the run is especially useful for archive-level contradiction mapping because summary/soak counters, state residue, and event rows disagree materially
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001`
- source class: small direct autoratchet run root
- total files: `17`
- total directories: `3`
- top-level entries:
  - `a1_inbox`
  - `events.jsonl`
  - `sequence_state.json`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets`
- notable absences:
  - no wrapper README
  - no `HARDMODE_METRICS.json`
  - no `sim/` directory

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/summary.json`
- sha256: `057a7c3afaf39b8dff788f0b93bedfe5f41391d2cfc27eecd589b1a7620d9510`
- size bytes: `589`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_QIT_AUTORATCHET_0001`
  - `steps_completed 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 2`
  - `unresolved_promotion_blocker_count 0`
  - `final_state_hash be67dd142f582e0c1f91fc55e15d76c4400ea66091669722bf1d289042b8c485`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/state.json`
- sha256: `be67dd142f582e0c1f91fc55e15d76c4400ea66091669722bf1d289042b8c485`
- size bytes: `14564`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 1`
  - `canonical_ledger_len 1`
  - `survivor_order_len 9`
  - `term_registry_len 1`
  - `kill_log_len 2`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `evidence_pending_len 1`
  - `sim_registry_len 2`
  - `sim_results_len 2`
  - `sim_promotion_status_len 2`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` dict contains one canonical key:
    - `S000001_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE -> E_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE`
  - `sim_promotion_status` marks both retained sims as `PARKED`
  - `kill_log` contains two `NEG_INFINITE_SET` kill signals

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/sequence_state.json`
- sha256: `8f146317a98587ce140bd676fa9c7bf72c5963ecfffa30d1a004615e9563e4bb`
- size bytes: `91`
- source class: sequence ledger
- sequence maxima:
  - `A0 2`
  - `A1 1`
  - `A2 0`
  - `B 1`
  - `SIM 2`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/events.jsonl`
- sha256: `d418e651b40486ebb342fa1bb0ce0ec5205797aaf4cec6bf493a5a28bce1293c`
- size bytes: `3003`
- line count: `6`
- source class: compact autoratchet event ledger
- event markers:
  - event kinds:
    - `a1_strategy_request_emitted`: `1`
    - `step_result`: `1`
    - `a1_generation_fail`: `4`
  - step values present:
    - `1`
  - referenced strategy packet:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packet:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim result packet count: `2`
  - repeated failure marker:
    - `a1_packet_zip_invalid::SEQUENCE_GAP` occurs in four retained generation-fail rows

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/soak_report.md`
- sha256: `7daf42eafcb39df65ade14f78ce2143d53bf76fbf3f263f3bae80a8c934c2f70`
- size bytes: `3177`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 0`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tag set: `NONE`
- retained contradiction:
  - the embedded event ledger still preserves one `step_result` row with `accepted 7`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/zip_packets`
- source class: embedded packet lattice
- file count: `6`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `1`
  - `A1_TO_A0_STRATEGY_ZIP`: `1`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `1`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `2`
- embedded strategy packet marker:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip` sha256 `69133caf09934fdfe0963ef644c2e1bd86d9f66b0b8b7e4050327449268e5e01`

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/a1_inbox`
- source class: mixed inbox lane
- top-level active packets:
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
- active packet count: `4`
- retained meaning:
  - the run stopped with a live strategy backlog still in the inbox

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001/a1_inbox/consumed`
- source class: consumed strategy residue
- file count: `1`
- packet marker:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - size bytes: `2334`
  - sha256: `2a91f3ec1997a158588b136497c029568aac4c0ef470b1758a1edf0bc7c62e51`
- lane relation to embedded strategy packet:
  - same filename as embedded `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - different bytes from embedded strategy packet hash `69133caf...`

## 3) Structural Map Of The Sources
### Segment A: autoratchet direct run root
- source anchors:
  - run root inventory
- source role:
  - preserves a direct small run with both consumed and still-active inbox lanes
- strong markers:
  - no wrapper README
  - `sequence_state.json` present
  - active backlog of packets `000002` through `000005`

### Segment B: zeroed headline versus accepted first step
- source anchors:
  - `summary.json`
  - `state.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves a top-line zeroed window on top of a real accepted first step
- strong markers:
  - summary and soak report both say `accepted_total 0`
  - state keeps `accepted_batch_count 1` and `canonical_ledger_len 1`
  - event ledger step-result row records `accepted 7`

### Segment C: sequence-gap failure surface
- source anchors:
  - `events.jsonl`
  - `a1_inbox/`
  - `sequence_state.json`
- source role:
  - preserves a queue/failure seam after the first consumed strategy packet
- strong markers:
  - four `a1_generation_fail` rows with `a1_packet_zip_invalid::SEQUENCE_GAP`
  - consumed lane has only `000001`
  - active inbox still holds `000002` through `000005`

### Segment D: parked-sim semantic burden under zero park/reject totals
- source anchors:
  - `state.json`
  - `summary.json`
  - `soak_report.md`
- source role:
  - preserves semantic burden even though no packets were parked or rejected
- strong markers:
  - `sim_promotion_status` has two entries and both are `PARKED`
  - `kill_log_len 2`
  - `evidence_pending_len 1`
  - `park_set_len 0` and `reject_log_len 0`

### Segment E: consumed-versus-embedded strategy identity split
- source anchors:
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source role:
  - preserves same-name packet divergence between input-residue and embedded transport surfaces
- strong markers:
  - consumed hash `2a91f3ec...`
  - embedded hash `69133caf...`
  - filename is identical while payload bytes differ

