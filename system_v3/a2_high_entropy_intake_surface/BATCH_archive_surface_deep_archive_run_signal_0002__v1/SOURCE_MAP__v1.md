# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0002__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_SIGNAL_PASS`
Batch scope: archive-only intake of `RUN_SIGNAL_0002`, bounded to the direct run root, core run-state surfaces, the root sequence ledger, the inbox consumed lane, and the embedded packet lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002`
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
  - this pass processes only the direct run `RUN_SIGNAL_0002` and does not reopen sibling runs
  - the archive value is a large clean-transport signal run with `50` coherent accepted steps, `300` retained SIM outputs, and zero packet parks or rejects
  - the run is especially useful for demotion lineage because accurate summary counts still end fail-closed on promotion truth, the final state hash is stronger than the retained event-lattice endpoint, no inbox-local sequence ledger survives, and the consumed strategy lane renumbers and diverges from the embedded lane
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0003`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002`
- source class: direct signal-run root
- total files: `507`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/summary.json`
- sha256: `390dfceb3878e000581815ddfb5fae39b5c99367a9691713fe431d640594e2fb`
- size bytes: `838`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_SIGNAL_0002`
  - `steps_completed 50`
  - `steps_requested 50`
  - `accepted_total 700`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 300`
  - `unresolved_promotion_blocker_count 300`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 50`
  - `unique_export_structural_digest_count 50`
  - `unique_strategy_digest_count 50`
  - `final_state_hash 3d779f220368f2fb34b84d48cef97d6501035922745e9a72d5788d19e9ccc46b`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 50 pass 0`
    - `T1_COMPOUND fail 150 pass 0`
    - `T2_OPERATOR fail 50 pass 0`
    - `T3_STRUCTURE fail 50 pass 0`
    - higher tiers all zero

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/state.json`
- sha256: `3d779f220368f2fb34b84d48cef97d6501035922745e9a72d5788d19e9ccc46b`
- size bytes: `860999`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 50`
  - `canonical_ledger_len 50`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 50`
  - `evidence_tokens_len 300`
  - `interaction_counts_len 200`
  - `kill_log_len 100`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 300`
  - `sim_registry_len 300`
  - `sim_results_len 300`
  - `survivor_ledger_len 702`
  - `survivor_order_len 702`
  - `term_registry_len 150`
  - `probe_meta_len 100`
  - `spec_meta_len 600`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains fifty canonical evidence keys from `S_CANON_A_0001` through `S_CANON_A_0050`
  - `kill_log` retains one hundred kill signals split evenly across:
    - `NEG_COMMUTATIVE_ASSUMPTION`
    - `NEG_CLASSICAL_TIME`
  - `park_set` is empty
  - `reject_log` is empty
  - all `300` `sim_promotion_status` entries are `PARKED`
  - retained sim ids split into six repeated families:
    - `BASE`
    - `BOUND`
    - `NEG_A`
    - `NEG_B`
    - `PERT`
    - `STRESS`

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/state.json.sha256`
- sha256: `961ea9bf28b563c53204cb0cecf603d1049765615a2fcd57f082086fd58981ca`
- size bytes: `77`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/sequence_state.json`
- sha256: `9bc303e490f8f2b8e0beb1c2bb32d3766d3f4ff51752f39a7d67e34a4164f5ba`
- size bytes: `87`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 51`
  - `A1 50`
  - `A2 0`
  - `B 50`
  - `SIM 300`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/a1_inbox`
- source class: inbox residue without local sequence ledger
- top-level entries:
  - `consumed/`
- retained meaning:
  - no `a1_inbox/sequence_state.json` exists for this run
  - the inbox retains only the consumed packet lane

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/events.jsonl`
- sha256: `a0024c668727c901163f2dca2dcc7f96d7688cba898c8933d1d26c35cc3907d5`
- size bytes: `172820`
- line count: `51`
- source class: large signal event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `50`
  - step values present:
    - `1` through `50`
  - retained digest diversity:
    - `50` distinct strategy digests
    - `50` distinct export content digests
    - `50` distinct export structural digests
  - retained pass progression:
    - each step preserves:
      - `accepted 14`
      - `parked 0`
      - `rejected 0`
      - `6` sim outputs
    - unresolved blocker counts rise linearly:
      - first five: `6`, `12`, `18`, `24`, `30`
      - last five: `276`, `282`, `288`, `294`, `300`
  - retained hash edge:
    - last result `state_hash_after` is `496d3845c18c79c5857529eb5f5cb0b59a3d6056191dec9c4655135f3f38b44d`
    - final `summary/state` hash is `3d779f220368f2fb34b84d48cef97d6501035922745e9a72d5788d19e9ccc46b`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/soak_report.md`
- sha256: `d9462ee0ce3a35bd81b4ba817820c6fbccff760b7e8db95360e5de97ebc12918`
- size bytes: `69205`
- source class: human-readable soak report
- report markers:
  - `cycle_count 50`
  - `accepted_total 700`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`
- retained event texture:
  - the last-event window preserves accepted result rows across steps `31` through `50`
  - each retained row shows `accepted 14`, `parked 0`, `rejected 0`, and `6` sim outputs
  - runtime-like `sim/sim_evidence_*` paths are preserved in all SIM outputs even though no local `sim/` directory exists

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/zip_packets`
- source class: embedded packet lattice
- file count: `451`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `50`
  - `A1_TO_A0_STRATEGY_ZIP`: `50`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `50`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `300`
- packet range markers:
  - first retained files:
    - `000001_A0_TO_A1_SAVE_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - last retained files:
    - `000296_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000297_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000298_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000299_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000300_SIM_TO_A0_SIM_RESULT_ZIP.zip`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002/a1_inbox/consumed`
- source class: renumbered consumed strategy residue
- file count: `50`
- packet range markers:
  - first retained files:
    - `400001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400005_A1_TO_A0_STRATEGY_ZIP.zip`
  - last retained files:
    - `400046_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400047_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400048_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400049_A1_TO_A0_STRATEGY_ZIP.zip`
    - `400050_A1_TO_A0_STRATEGY_ZIP.zip`
- cross-lane comparison:
  - same-position byte-identical matches: `1`
  - same-position byte mismatches: `49`
  - the only byte-identical pair is step `1`
