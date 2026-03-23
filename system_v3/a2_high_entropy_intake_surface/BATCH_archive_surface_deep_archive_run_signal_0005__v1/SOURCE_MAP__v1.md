# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_SIGNAL_PASS`
Batch scope: archive-only intake of `RUN_SIGNAL_0005`, bounded to the direct run root, core run-state surfaces, the root sequence ledger, two audit overlays, the inbox consumed lane, and the embedded packet lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005`
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
  - this pass processes only the direct run `RUN_SIGNAL_0005` and does not reopen sibling runs
  - the archive value is a repaired signal-plus-audit run where summary, state, sequence, and event counts all align on the same `60`-pass A1 lattice
  - the run remains useful for demotion lineage because replay audit is still internally deterministic yet diverges from both the final run snapshot hash and the event-lattice endpoint, and the consumed strategy lane still renumbers and diverges from the embedded lane
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005_bundle.zip`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/summary.json`
- sha256: `cf4f00bb80097753b1c2cfc73eb4bb58a4633e03046ae56b6b50a179049c858e`
- size bytes: `838`
- source class: direct final snapshot summary
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/state.json`
- sha256: `0045ff3fdb8a39572123eef7bfb071d583d60326371eb0d6a08be8bc36307f93`
- size bytes: `1233046`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/state.json.sha256`
- sha256: `a98042d455575b628cd455ce6f083cafcea4740941026f2e8279f96169f824fa`
- size bytes: `77`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/sequence_state.json`
- sha256: `5b887e6db23db96f19591715bee40a0bc906caf83f7b6dc9a9a8ac5ee99e283c`
- size bytes: `87`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 61`
  - `A1 60`
  - `A2 0`
  - `B 60`
  - `SIM 360`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/SIGNAL_AUDIT.json`
- sha256: `5e3df34ffdf1d02a87f8cc3772ec13b500ef686b00a6d4591289024ec65d2ed6`
- size bytes: `732`
- source class: compact structural audit overlay
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
  - `killed_math_count` is `null`
  - pending by kind:
    - `CANON_PERMIT 60`
  - final state hash matches `summary.json` and `state.json`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/REPLAY_AUDIT.json`
- sha256: `ec4d4492f3f302b7b6172a5a47e47110dc765fb928609ddce4d7b58043bbfa8e`
- size bytes: `411128`
- source class: reconstructive replay audit overlay
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
  - replay final hash does not match `summary/state` final hash

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/a1_inbox`
- source class: inbox residue without local sequence ledger
- top-level entries:
  - `consumed/`
- retained meaning:
  - no `a1_inbox/sequence_state.json` exists for this run
  - the inbox retains only the consumed packet lane

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/events.jsonl`
- sha256: `37f919acb2d0f92473f91a6872fe1a2fa5d9cfaf2872c6b469fbed0bf9cf6a86`
- size bytes: `207320`
- line count: `61`
- source class: aligned signal event ledger
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
    - final `summary/state` hash is `0045ff3fdb8a39572123eef7bfb071d583d60326371eb0d6a08be8bc36307f93`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/soak_report.md`
- sha256: `6494ed7321272f80e96691e31b9d5cce5aab545d61bd2b48e796972179200f2a`
- size bytes: `69205`
- source class: human-readable soak report
- report markers:
  - `cycle_count 60`
  - `accepted_total 960`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/zip_packets`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/a1_inbox/consumed`
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
