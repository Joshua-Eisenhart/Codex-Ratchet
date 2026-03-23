# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_SIGNAL_BUNDLE_PASS`
Batch scope: archive-only intake of `RUN_SIGNAL_0005_bundle.zip`, bounded to the zip container, its embedded `RUN_SIGNAL_0005/` export root, core run-state surfaces, audit overlays, strategy/outbox/snapshot/report families, embedded sim evidence bodies, the inbox consumed lane, and the embedded packet lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
  - embedded run family under zip root:
    - `RUN_SIGNAL_0005/summary.json`
    - `RUN_SIGNAL_0005/state.json`
    - `RUN_SIGNAL_0005/state.json.sha256`
    - `RUN_SIGNAL_0005/events.jsonl`
    - `RUN_SIGNAL_0005/sequence_state.json`
    - `RUN_SIGNAL_0005/soak_report.md`
    - `RUN_SIGNAL_0005/SIGNAL_AUDIT.json`
    - `RUN_SIGNAL_0005/REPLAY_AUDIT.json`
    - `RUN_SIGNAL_0005/a1_inbox/`
    - `RUN_SIGNAL_0005/a1_strategies/`
    - `RUN_SIGNAL_0005/outbox/`
    - `RUN_SIGNAL_0005/reports/`
    - `RUN_SIGNAL_0005/sim/`
    - `RUN_SIGNAL_0005/snapshots/`
    - `RUN_SIGNAL_0005/zip_packets/`
- reason for bounded family batch:
  - this pass processes only the zipped bundle `RUN_SIGNAL_0005_bundle.zip` and does not reopen sibling run roots
  - the archive value is that the bundle is materially fuller than the direct run-root pattern: it is a self-contained export kit with local sim evidence bodies, strategy JSONs, compile/eval reports, snapshots, and outbox blocks
  - the bundle is especially useful for demotion lineage because runtime-facing counts are aligned, but both the event-lattice endpoint and the deterministic replay audit still diverge from the final snapshot hash
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_A1_PACKET_EMPTY`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- sha256: `d42708222c0c771394bf98def2002abfece88811a0247a8436a28594ab790e78`
- size bytes: `5008299`
- source class: zipped self-contained signal bundle
- zip container markers:
  - total file members: `1271`
  - total directory members: `9`
  - single top-level root:
    - `RUN_SIGNAL_0005/`
  - embedded file-family counts:
    - `a1_inbox`: `61`
    - `a1_strategies`: `60`
    - `outbox`: `60`
    - `reports`: `120`
    - `sim`: `360`
    - `snapshots`: `60`
    - `zip_packets`: `541`
  - embedded noise:
    - root `.DS_Store`
    - `a1_inbox/.DS_Store`

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/summary.json`
- source class: embedded final snapshot summary
- summary markers:
  - `run_id RUN_SIGNAL_0005`
  - `steps_completed 60`
  - `steps_requested 60`
  - `accepted_total 960`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 360`
  - `unresolved_promotion_blocker_count 360`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 60`
  - `unique_export_structural_digest_count 60`
  - `unique_strategy_digest_count 60`
  - `final_state_hash 0045ff3fdb8a39572123eef7bfb071d583d60326371eb0d6a08be8bc36307f93`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 60 pass 0`
    - `T1_COMPOUND fail 180 pass 0`
    - `T2_OPERATOR fail 60 pass 0`
    - `T3_STRUCTURE fail 60 pass 0`
    - higher tiers all zero

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/state.json`
- source class: embedded final snapshot state
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
  - `evidence_pending` is an object with `60` keys
  - `kill_log` retains `240` kill signals split evenly across:
    - `NEG_COMMUTATIVE_ASSUMPTION`
    - `NEG_CLASSICAL_TIME`
  - `park_set` is empty
  - `reject_log` is empty
  - all `360` `sim_promotion_status` entries are `PARKED`

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/state.json.sha256`
- source class: embedded state integrity sidecar
- integrity result:
  - declared hash matches embedded `state.json` sha256
  - declared hash matches embedded `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/sequence_state.json`
- source class: embedded full run sequence ledger
- sequence maxima:
  - `A0 61`
  - `A1 60`
  - `A2 0`
  - `B 60`
  - `SIM 360`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/SIGNAL_AUDIT.json`
- source class: embedded compact structural audit overlay
- audit markers:
  - `run_id RUN_SIGNAL_0005`
  - `steps_completed 60`
  - `accepted_total 960`
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
  - `killed_math_count` absent/null-equivalent
  - pending by kind:
    - `CANON_PERMIT 60`
  - final state hash matches embedded `summary.json` and `state.json`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/REPLAY_AUDIT.json`
- source class: embedded reconstructive replay audit overlay
- audit markers:
  - determinism check:
    - `pass true`
    - first/second decision traces match exactly
    - first/second emitted artifact hashes match exactly
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
    - `ed1a34d2fb3b0e18312f868861abbb289e50e08ef16f2fbf7afe54d9b84cc3ae`
  - replay final hash does not match embedded `summary/state` final hash

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/events.jsonl`
- source class: embedded aligned event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `60`
  - step values present:
    - `1` through `60`
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
    - last result `state_hash_after` is `299c9c26d502dd7cc000d4503130cc56c8c9e7b0b3a0c34302dbb46ef28a46fc`
    - final embedded `summary/state` hash is `0045ff3fdb8a39572123eef7bfb071d583d60326371eb0d6a08be8bc36307f93`

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/soak_report.md`
- source class: embedded human-readable soak report
- report markers:
  - `cycle_count 60`
  - `accepted_total 960`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/a1_inbox/`
- source class: embedded inbox residue
- top-level entries:
  - `.DS_Store`
  - `consumed/`
- retained meaning:
  - no embedded inbox-local `sequence_state.json`
  - the inbox retains sixty consumed strategy packets plus Finder noise

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/a1_strategies/`
- source class: embedded strategy export family
- family markers:
  - `60` strategy JSON files
  - file range:
    - `a1_strategy_0001.json`
    - `...`
    - `a1_strategy_0060.json`
  - retained meaning:
    - the bundle keeps per-step strategy JSONs rather than only packetized strategy residue

### Source 12
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/outbox/`
- source class: embedded export-block family
- family markers:
  - `60` export-block text files
  - file range:
    - `export_block_0001.txt`
    - `...`
    - `export_block_0060.txt`
  - retained sample meaning:
    - export blocks preserve compiled batch proposals with explicit `TARGET THREAD_B_ENFORCEMENT_KERNEL`, branch-track bindings, and negative-class kill bindings

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/snapshots/`
- source class: embedded save-snapshot family
- family markers:
  - `60` snapshot text files
  - file range:
    - `snapshot_0001.txt`
    - `...`
    - `snapshot_0060.txt`
  - retained sample meaning:
    - snapshots preserve `THREAD_S_SAVE_SNAPSHOT v2` save-state bodies rather than only final summary counters

### Source 14
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/reports/`
- source class: embedded compile/eval report family
- family markers:
  - `120` report files split into:
    - `60` `a0_compile_*.json`
    - `60` `b_report_*.txt`
  - retained sample meaning:
    - the bundle keeps both compile-time structural digest reports and per-export evaluation reports

### Source 15
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/sim/`
- source class: embedded local sim evidence family
- family markers:
  - `360` sim evidence text files
  - file range:
    - `sim_evidence_0001_001.txt`
    - `...`
    - `sim_evidence_0060_006.txt`
  - retained meaning:
    - unlike the thinner direct run-root pattern, the bundle carries local evidence bodies for all retained SIM outputs

### Source 16
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/zip_packets/`
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

### Source 17
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`
- zip member path: `RUN_SIGNAL_0005/a1_inbox/consumed/`
- source class: embedded consumed strategy lane
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
