# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0003__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_SIGNAL_PASS`
Batch scope: archive-only intake of `RUN_SIGNAL_0003`, bounded to the direct run root, core run-state surfaces, the root sequence ledger, the inbox consumed lane, and the embedded packet lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003`
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
  - this pass processes only the direct run `RUN_SIGNAL_0003` and does not reopen sibling runs
  - the archive value is a mid-scale clean-transport signal run with `30` coherent accepted steps, `180` retained SIM outputs, and zero packet parks or rejects
  - the run is especially useful for demotion lineage because accurate summary counts still end fail-closed on promotion truth, negative-kill retention inflates through paired `S_SIM_*` and `S_MATH_ALT_*` entries, no inbox-local sequence ledger survives, and the consumed strategy lane renumbers and diverges from the embedded lane
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0004`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003`
- source class: direct signal-run root
- total files: `307`
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
  - no local `sim/` directory

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/summary.json`
- sha256: `3ddf742bd0830d5fdab8fc971316e79f26caa7945d07d6bd6dd0e201c8e89527`
- size bytes: `837`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_SIGNAL_0003`
  - `steps_completed 30`
  - `steps_requested 30`
  - `accepted_total 480`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 180`
  - `unresolved_promotion_blocker_count 180`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 30`
  - `unique_export_structural_digest_count 30`
  - `unique_strategy_digest_count 30`
  - `final_state_hash d4b56764f753136a7eaa89ef93695f5245fa4b3e1dcd7a21d7abe9d183c999d2`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 30 pass 0`
    - `T1_COMPOUND fail 90 pass 0`
    - `T2_OPERATOR fail 30 pass 0`
    - `T3_STRUCTURE fail 30 pass 0`
    - higher tiers all zero

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/state.json`
- sha256: `d4b56764f753136a7eaa89ef93695f5245fa4b3e1dcd7a21d7abe9d183c999d2`
- size bytes: `598153`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 30`
  - `canonical_ledger_len 30`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 30`
  - `evidence_tokens_len 180`
  - `interaction_counts_len 120`
  - `kill_log_len 120`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 180`
  - `sim_registry_len 180`
  - `sim_results_len 180`
  - `survivor_ledger_len 482`
  - `survivor_order_len 482`
  - `term_registry_len 90`
  - `probe_meta_len 60`
  - `spec_meta_len 420`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains thirty canonical evidence keys from `S_CANON_A_0001` through `S_CANON_A_0030`
  - `kill_log` retains one hundred twenty kill signals split evenly across:
    - `NEG_COMMUTATIVE_ASSUMPTION`
    - `NEG_CLASSICAL_TIME`
  - each negative token is duplicated through paired ids:
    - `S_SIM_NEG_A_*` with `S_MATH_ALT_A_*`
    - `S_SIM_NEG_B_*` with `S_MATH_ALT_B_*`
  - `park_set` is empty
  - `reject_log` is empty
  - all `180` `sim_promotion_status` entries are `PARKED`

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/state.json.sha256`
- sha256: `8010d4c96c996922dcb15334474336e029e3fcf79847964f97fa54d324e355c6`
- size bytes: `77`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/sequence_state.json`
- sha256: `968426fc486cf13a8d4a7b973c88d14e7cc2e5b64538b79bc92ead94ddeb9956`
- size bytes: `87`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 31`
  - `A1 30`
  - `A2 0`
  - `B 30`
  - `SIM 180`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/a1_inbox`
- source class: inbox residue without local sequence ledger
- top-level entries:
  - `consumed/`
- retained meaning:
  - no `a1_inbox/sequence_state.json` exists for this run
  - the inbox retains only the consumed packet lane

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/events.jsonl`
- sha256: `a7122fff4230acbff83f888bb96affe4471430d3ce6745df02d29336a83b24e8`
- size bytes: `103820`
- line count: `31`
- source class: signal event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `30`
  - step values present:
    - `1` through `30`
  - retained digest diversity:
    - `30` distinct strategy digests
    - `30` distinct export content digests
    - `30` distinct export structural digests
  - retained pass progression:
    - each step preserves:
      - `accepted 16`
      - `parked 0`
      - `rejected 0`
      - `6` sim outputs
    - unresolved blocker counts rise linearly:
      - first five: `6`, `12`, `18`, `24`, `30`
      - last five: `156`, `162`, `168`, `174`, `180`
  - retained hash edge:
    - last result `state_hash_after` is `1aadd5aea64670da19dc31a9b0c96c60ba720ffaecb6fde52a16c2c2e5a55c8b`
    - final `summary/state` hash is `d4b56764f753136a7eaa89ef93695f5245fa4b3e1dcd7a21d7abe9d183c999d2`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/soak_report.md`
- sha256: `0a222baa679098e9ad902b31115df5829d3a9886108cf1073b9bd1303f97844c`
- size bytes: `69199`
- source class: human-readable soak report
- report markers:
  - `cycle_count 30`
  - `accepted_total 480`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`
- retained event texture:
  - the last-event window preserves accepted result rows across steps `11` through `30`
  - each retained row shows `accepted 16`, `parked 0`, `rejected 0`, and `6` sim outputs
  - runtime-like `sim/sim_evidence_*` paths are preserved in all SIM outputs even though no local `sim/` directory exists

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/zip_packets`
- source class: embedded packet lattice
- file count: `271`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `30`
  - `A1_TO_A0_STRATEGY_ZIP`: `30`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `30`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `180`
- packet range markers:
  - first retained files:
    - `000001_A0_TO_A1_SAVE_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - last retained files:
    - `000176_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000177_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000178_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000179_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000180_SIM_TO_A0_SIM_RESULT_ZIP.zip`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003/a1_inbox/consumed`
- source class: renumbered consumed strategy residue
- file count: `30`
- packet range markers:
  - first retained files:
    - `400001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400005_A1_TO_A0_STRATEGY_ZIP.zip`
  - last retained files:
    - `400026_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400027_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400028_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400029_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400030_A1_TO_A0_STRATEGY_ZIP.zip`
- cross-lane comparison:
  - same-position byte-identical matches: `1`
  - same-position byte mismatches: `29`
  - the only byte-identical pair is step `1`
