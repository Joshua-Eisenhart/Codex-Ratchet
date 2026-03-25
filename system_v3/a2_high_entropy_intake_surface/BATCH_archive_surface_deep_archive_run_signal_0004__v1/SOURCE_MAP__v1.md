# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0004__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_SIGNAL_PASS`
Batch scope: archive-only intake of `RUN_SIGNAL_0004`, bounded to the direct run root, core run-state surfaces, the root sequence ledger, two audit overlays, the inbox consumed lane, and the embedded packet lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004`
  - core run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
    - `zip_packets/`
  - audit overlays:
    - `SIGNAL_AUDIT.json`
    - `REPLAY_AUDIT.json`
  - inbox residue surfaces:
    - `a1_inbox/`
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the direct run `RUN_SIGNAL_0004` and does not reopen sibling runs
  - the archive value is a hybrid signal-plus-audit run where summary compresses the object to `40` steps while state, sequence, packet lanes, and replay audit preserve a larger `60`-packet A1 lattice
  - the run is especially useful for demotion lineage because two audit surfaces now coexist with runtime-like state, and the replay audit is internally deterministic yet still diverges from both the summary/state final hash and the event-lattice endpoint
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004`
- source class: direct signal-run root with audit overlays
- total files: `609`
- total directories: `3`
- top-level entries:
  - `REPLAY_AUDIT.json`
  - `SIGNAL_AUDIT.json`
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
  - no local `sim/` directory

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/summary.json`
- sha256: `5be0b457dd6f58b343714a92fdfa9432bc7f194083e696dfcea95b66d22c1fd7`
- size bytes: `838`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_SIGNAL_0004`
  - `steps_completed 40`
  - `steps_requested 40`
  - `accepted_total 640`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 360`
  - `unresolved_promotion_blocker_count 360`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 40`
  - `unique_export_structural_digest_count 40`
  - `unique_strategy_digest_count 40`
  - `final_state_hash 6e07a40694f3cbb4992f8dccad32ffc5fef81f612f788d7109764cdcef62c4fd`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 60 pass 0`
    - `T1_COMPOUND fail 180 pass 0`
    - `T2_OPERATOR fail 60 pass 0`
    - `T3_STRUCTURE fail 60 pass 0`
    - higher tiers all zero

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/state.json`
- sha256: `6e07a40694f3cbb4992f8dccad32ffc5fef81f612f788d7109764cdcef62c4fd`
- size bytes: `1233037`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 60`
  - `canonical_ledger_len 60`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 60`
  - `evidence_tokens_len 360`
  - `interaction_counts_len 240`
  - `kill_log_len 240`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 360`
  - `sim_registry_len 360`
  - `sim_results_len 360`
  - `survivor_ledger_len 962`
  - `survivor_order_len 962`
  - `term_registry_len 180`
  - `probe_meta_len 120`
  - `spec_meta_len 840`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains `60` canonical evidence items
  - `kill_log` retains `240` kill signals split evenly across:
    - `NEG_COMMUTATIVE_ASSUMPTION`
    - `NEG_CLASSICAL_TIME`
  - `park_set` is empty
  - `reject_log` is empty
  - all `360` `sim_promotion_status` entries are `PARKED`

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/state.json.sha256`
- sha256: `661f803c850b1290e782b0bd35672646e5868db68e540b5e9196a9934a7bdb45`
- size bytes: `77`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/sequence_state.json`
- sha256: `ba088537e181c3934ae8fc3a782b3b0e19516739babef30849df9fb8e0adaea5`
- size bytes: `87`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 61`
  - `A1 60`
  - `A2 0`
  - `B 60`
  - `SIM 360`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/SIGNAL_AUDIT.json`
- sha256: `202043f93c50c010685a7abb2e730ac3b679d24f5e9e5c161b22cb586606d7f5`
- size bytes: `756`
- source class: compact structural audit overlay
- audit markers:
  - `run_id RUN_SIGNAL_0004`
  - `steps_completed 40`
  - `accepted_total 640`
  - `sim_registry_count 360`
  - `canonical_ledger_len 60`
  - `survivor_count 962`
  - `term_registry_count 180`
  - branch tracks:
    - `DENSITY_CHANNEL 180`
    - `OPERATOR_ORDER 180`
    - `TRACE_STABILITY 180`
  - kill kind counts:
    - `MATH_DEF 120`
    - `SIM_SPEC 120`
  - pending by kind:
    - `CANON_PERMIT 60`
  - final state hash matches `summary.json` and `state.json`

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/REPLAY_AUDIT.json`
- sha256: `f32906e6adcc373780225333f29faca9613a1a13a7411c7b18102081faaa5dc3`
- size bytes: `411128`
- source class: reconstructive replay audit overlay
- audit markers:
  - determinism check:
    - `pass true`
    - first/second decision traces match exactly
    - first/second emitted artifacts hashes match exactly
  - replay event count: `541`
  - replay outcome counts:
    - `OK 60`
    - `PARK 481`
  - replay directions:
    - `FORWARD 120`
    - `BACKWARD 421`
  - replay source layers:
    - `A0 61`
    - `A1 60`
    - `B 60`
    - `SIM 360`
  - replay reasons:
    - `REPLAY_PREREQ_MISSING_FORWARD`
    - `MISSING_FORWARD_SEQUENCE:A0:1`
    - `SEQUENCE_GAP`
  - replay final hash:
    - `e840db7cc1e0b4eaa201b0fef922b7642e9a33ec3356389496592aa7b2df6e52`
  - replay final hash does not match `summary/state` final hash

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/a1_inbox`
- source class: inbox residue without local sequence ledger
- top-level entries:
  - `consumed/`
- retained meaning:
  - no `a1_inbox/sequence_state.json` exists for this run
  - the inbox retains only the consumed packet lane

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/events.jsonl`
- sha256: `fc29f3c39c7b128033f2a99a37e7d5759e6fdc0d5a2b1d85f7f3f67bdb507c5e`
- size bytes: `207311`
- line count: `61`
- source class: compressed signal event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `60`
  - visible step values present:
    - `1` through `40`
  - repeated step compression:
    - steps `1` through `20` appear twice each
    - steps `21` through `40` appear once each
  - retained digest diversity:
    - `60` distinct strategy digests
    - `60` distinct export content digests
    - `60` distinct export structural digests
  - retained pass progression:
    - each result row preserves:
      - `accepted 16`
      - `parked 0`
      - `rejected 0`
      - `6` sim outputs
    - total accepted across retained rows: `960`
    - unresolved blockers rise from `6` to `360`
  - retained hash edge:
    - last result `state_hash_after` is `d08f6d2d01f290cdc54769e3cd6f4d0367ff640b33942a7758782702ac988ea3`
    - final `summary/state` hash is `6e07a40694f3cbb4992f8dccad32ffc5fef81f612f788d7109764cdcef62c4fd`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/soak_report.md`
- sha256: `1e8a5e9b9ad56201534621228d83f032d91f45731252a92babfa1fa985795b29`
- size bytes: `69205`
- source class: human-readable soak report
- report markers:
  - `cycle_count 40`
  - `accepted_total 640`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/zip_packets`
- source class: embedded packet lattice
- file count: `541`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `60`
  - `A1_TO_A0_STRATEGY_ZIP`: `60`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `60`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `360`
- packet range markers:
  - first retained files:
    - `000001_A0_TO_A1_SAVE_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - last retained files:
    - `000356_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000357_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000358_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000359_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000360_SIM_TO_A0_SIM_RESULT_ZIP.zip`

### Source 12
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004/a1_inbox/consumed`
- source class: renumbered consumed strategy residue
- file count: `60`
- packet range markers:
  - first retained files:
    - `400001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400005_A1_TO_A0_STRATEGY_ZIP.zip`
  - last retained files:
    - `400056_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400057_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400058_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400059_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400060_A1_TO_A0_STRATEGY_ZIP.zip`
- cross-lane comparison:
  - same-position byte-identical matches: `1`
  - same-position byte mismatches: `59`
  - the only byte-identical pair is step `1`
