# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0004__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_QIT_AUTORATCHET_PASS`
Batch scope: archive-only intake of `RUN_QIT_AUTORATCHET_0004`, bounded to the direct run root, core run-state surfaces, both retained sequence ledgers, the embedded packet lattice, and the consumed strategy lane
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004`
  - core run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
    - `zip_packets/`
  - inbox residue surfaces:
    - `a1_inbox/sequence_state.json`
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the direct run `RUN_QIT_AUTORATCHET_0004` and does not reopen sibling runs
  - the archive value is an eight-pass queue-drained autoratchet run whose summary again collapses both step count and digest diversity below what the retained result rows preserve
  - the run is especially useful for demotion lineage because it adds a mixed `A_`/`Z_` semantic namespace drift on top of growing park/reject burden and full-family packet-byte divergence
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004`
- source class: direct autoratchet run root
- total files: `48`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/summary.json`
- sha256: `a2b88a76270e5377850695df885523210f8f6fd08b96e0553dda84a7633c2f39`
- size bytes: `834`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_QIT_AUTORATCHET_0004`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 3`
  - `parked_total 2`
  - `rejected_total 2`
  - `sim_registry_count 18`
  - `unresolved_promotion_blocker_count 18`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 1`
  - `unique_export_structural_digest_count 1`
  - `unique_strategy_digest_count 1`
  - `final_state_hash 8041bffecfa4cb56e2600f99a6544db64a2d2b0bf1724ff1954f258ab5678acd`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 10 pass 0`
    - `T1_COMPOUND fail 8 pass 0`
    - higher tiers all zero

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/state.json`
- sha256: `8041bffecfa4cb56e2600f99a6544db64a2d2b0bf1724ff1954f258ab5678acd`
- size bytes: `86276`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 8`
  - `canonical_ledger_len 8`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 4`
  - `evidence_tokens_len 8`
  - `interaction_counts_len 5`
  - `kill_log_len 6`
  - `park_set_len 13`
  - `reject_log_len 26`
  - `sim_promotion_status_len 18`
  - `sim_registry_len 18`
  - `sim_results_len 8`
  - `survivor_ledger_len 44`
  - `survivor_order_len 44`
  - `term_registry_len 4`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains four canonical evidence obligations with mixed namespace prefixes:
    - `S000001_Z_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE`
    - `S000002_Z_CANON_DENSITY_MATRIX`
    - `S000003_A_CANON_POSITIVE`
    - `S000004_A_CANON_SEMIDEFINITE`
  - `kill_log` retains six kill signals with tokens:
    - `NEG_INFINITE_SET` for `S000001_Z_*` and `S000003_Z_*`
    - `NEG_COMMUTATIVE_ASSUMPTION` for `S000002_Z_*`
  - `park_set` retains thirteen parked items with tag mix:
    - `NEAR_REDUNDANT` x `12`
    - `UNDEFINED_TERM_USE` x `1`
  - `reject_log` retains twenty-six reject rows with tag mix:
    - `SCHEMA_FAIL` x `13`
    - `NEAR_REDUNDANT` x `12`
    - `UNDEFINED_TERM_USE` x `1`
  - all `18` `sim_promotion_status` entries are `PARKED`
  - the retained semantic ids split across `A_` and `Z_` namespace prefixes

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/sequence_state.json`
- sha256: `cdc81588d3ed195aa4a8d20fe3487e4c3bca408dac995a6982628701389ea8ac`
- size bytes: `91`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 9`
  - `A1 8`
  - `A2 0`
  - `B 8`
  - `SIM 8`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/a1_inbox/sequence_state.json`
- sha256: `aa3ddfa992d46663642542d9af8a70d6e269ef1478c28d817114185739a7e86b`
- size bytes: `34`
- source class: inbox-local A1 sequence ledger
- retained marker:
  - `RUN_QIT_AUTORATCHET_0004|A1 -> 8`
- relation to root sequence ledger:
  - root and inbox ledgers are not identical JSON shapes
  - both preserve the same terminal A1 sequence max of `8`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/events.jsonl`
- sha256: `016c4aaaff6a12aee452e98e37d83f268ec8bb24ad90d2ce5484a0ecef7e8423`
- size bytes: `12984`
- line count: `9`
- source class: compact autoratchet event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `8`
  - step values present:
    - `1`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000006_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000007_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000008_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000004_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000005_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000006_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000007_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000008_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000009_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim outputs total: `8`
  - retained digest diversity:
    - `8` distinct strategy digests
    - `8` distinct export content digests
    - `5` distinct export structural digests
- retained pass progression:
  - pass 1:
    - `accepted 7`
    - `parked 0`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 2`
  - pass 2:
    - `accepted 7`
    - `parked 0`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 4`
  - pass 3:
    - `accepted 9`
    - `parked 3`
    - `rejected 3`
    - `unresolved_promotion_blocker_count 7`
  - pass 4:
    - `accepted 7`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 10`
  - pass 5:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 12`
  - pass 6:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 14`
  - pass 7:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 16`
  - pass 8:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 18`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/soak_report.md`
- sha256: `7c71a7735a134d7f432bfe38a25acf52f4a340949776f8e3d1cffea1f60b7317`
- size bytes: `13174`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 3`
  - `parked_total 2`
  - `rejected_total 2`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `SCHEMA_FAIL 6`
- retained event texture:
  - the last-event window preserves eight retained result rows over strategy packets `000001` through `000008`
  - the first two retained rows show `accepted 7`
  - the third retained row shows `accepted 9`, `parked 3`, `rejected 3`
  - the final four retained rows all show `accepted 3`, `parked 2`, `rejected 2`

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/zip_packets`
- source class: embedded packet lattice
- file count: `33`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `8`
  - `A1_TO_A0_STRATEGY_ZIP`: `8`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `8`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `8`
- embedded strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> f8058669e4d10d3b9fa0f8884cb019ded3938927110e38c26fe2ff1a3c49ac57`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> fce5f73e71f671f6bfae2ef127292210b5ad22481f92bdda558156d8d3d58d13`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> edcd3227566999a957b27725260037ce17a3053c7600828b60dbdabce47519b7`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> 6410bc5f1eaa30373771af289d5e9c76f7ad64ec5cb7c1fd0da60e5b74aaeb08`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> fb93c29138bfe9242c03d879ed4b5911b70f39f0046e77d720bfcff8cd62bf8d`
  - `000006_A1_TO_A0_STRATEGY_ZIP.zip -> f515d14e44d9181ca2bc4543c2ce98a68164be7c8cac6ab4f28e687a34e7963e`
  - `000007_A1_TO_A0_STRATEGY_ZIP.zip -> 61110c1c292f0643a1c1bb29de0ac08b60e61a427eeed602f8452a24525e02d7`
  - `000008_A1_TO_A0_STRATEGY_ZIP.zip -> 5ead624b233434ed3ec4c7525d80736fa5bef9110973506f58bb9af4dfe0ecbc`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004/a1_inbox/consumed`
- source class: fully consumed strategy residue
- file count: `8`
- consumed strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> 9a7bd8fe854b1050a59c85c7e6f849424ae759f42c75ad4ca39d81704e1aa00b`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 1d89d1494d2182ed51bbed720cfc499e532906c34c4151538e26ab041d48bd96`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 3e8750b215b47753315d714facfda01cf121392f6efe272a4da651cd793a6435`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> 446d4efb4696ec1d11b59a2695b71cac047ddb8b2bec0dce82d30a4f8fcb5a6d`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 36f33683039440c382e80f10914602ccb118de4e91b250e16b9eb15d2bd4aabf`
  - `000006_A1_TO_A0_STRATEGY_ZIP.zip -> 96ff305fd1bc93c00cf0b3129ada5da5345a04d48322599e7055d666d63f124a`
  - `000007_A1_TO_A0_STRATEGY_ZIP.zip -> e6fe9744c377d8ec3ce211d52f9f23fa61454ec1c0d1d2462d31772803d0267c`
  - `000008_A1_TO_A0_STRATEGY_ZIP.zip -> fb64f1955651db0c02eada309d87403c859f1382da723e028e9352a3598e8989`
- lane relation to embedded strategy packets:
  - same eight filenames appear in both consumed and embedded lanes
  - all eight same-name pairs differ byte-for-byte
  - no live unconsumed strategy packets remain in `a1_inbox/`

## 3) Structural Map Of The Sources
### Segment A: queue-drained eight-pass autoratchet run
- source anchors:
  - run root inventory
  - `a1_inbox/consumed/`
  - `a1_inbox/sequence_state.json`
- source role:
  - preserves a direct autoratchet run captured after eight strategy packets were consumed and the inbox drained
- strong markers:
  - eight consumed strategy packets survive
  - no live strategy packet files remain in `a1_inbox/`
  - no wrapper README is present

### Segment B: one-step headline over eight retained passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves stronger step compression where eight retained result passes collapse into one nominal completed step
- strong markers:
  - `steps_completed 1`
  - `events.jsonl` keeps eight result-shaped rows after the initial request row
  - all retained result rows use step value `1`

### Segment C: digest-collapse summary over multi-digest history
- source anchors:
  - `summary.json`
  - `events.jsonl`
- source role:
  - preserves a stronger collapse of digest diversity in the headline summary
- strong markers:
  - summary records `unique_strategy_digest_count 1`
  - summary records both export digest counts as `1`
  - retained result rows preserve `8` distinct strategy digests, `8` export content digests, and `5` export structural digests

### Segment D: parked and rejected semantic burden under final-window counters
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves a larger parked/reject burden than the final headline window suggests
- strong markers:
  - `summary.json` ends at `parked_total 2` and `rejected_total 2`
  - `state.json` keeps `park_set_len 13`, `reject_log_len 26`, and `kill_log_len 6`
  - all `18` sim promotion statuses are `PARKED`

### Segment E: namespace drift inside retained semantic ids
- source anchors:
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves a mixed naming regime where semantic ids split across `A_` and `Z_` prefixes inside the same run family
- strong markers:
  - evidence keys mix `S000003_A_*` and `S000001_Z_*`
  - sim ids in retained result rows mix `A_SIM_*` and `Z_SIM_*`
  - summary offers no explicit explanation for the namespace split

### Segment F: same-name strategy-family instability across eight pairs
- source anchors:
  - `zip_packets/`
  - `a1_inbox/consumed/`
- source role:
  - preserves a full eight-packet family where filename identity is never enough to recover byte identity
- strong markers:
  - same names `000001` through `000008` exist in both lanes
  - all eight consumed-versus-embedded pairs diverge byte-for-byte

