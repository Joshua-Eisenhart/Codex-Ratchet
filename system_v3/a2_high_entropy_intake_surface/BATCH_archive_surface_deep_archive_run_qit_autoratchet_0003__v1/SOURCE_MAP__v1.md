# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0003__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_QIT_AUTORATCHET_PASS`
Batch scope: archive-only intake of `RUN_QIT_AUTORATCHET_0003`, bounded to the direct run root, core run-state surfaces, both retained sequence ledgers, the embedded packet lattice, and the consumed strategy lane
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003`
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
  - this pass processes only the direct run `RUN_QIT_AUTORATCHET_0003` and does not reopen sibling runs
  - the archive value is a queue-drained six-pass autoratchet run whose summary collapses both step count and unique digest counts below what the retained result rows preserve
  - the run is especially useful for demotion lineage because it combines six same-name packet mismatches, a growing parked/reject burden, and missing local sim evidence bodies
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0004`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003`
- source class: direct autoratchet run root
- total files: `40`
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
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/summary.json`
- sha256: `0cb670beb0ad149b601aa1d5aa12b6a579dbfcfcdd4ee58721d39ab2bcaf003f`
- size bytes: `833`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_QIT_AUTORATCHET_0003`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 3`
  - `parked_total 2`
  - `rejected_total 2`
  - `sim_registry_count 14`
  - `unresolved_promotion_blocker_count 14`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 1`
  - `unique_export_structural_digest_count 1`
  - `unique_strategy_digest_count 1`
  - `final_state_hash 5f5011708ccc3f070f7c97e35c68767aea9926d412a9cf22b8e7adef060818f2`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 8 pass 0`
    - `T1_COMPOUND fail 6 pass 0`
    - higher tiers all zero

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/state.json`
- sha256: `5f5011708ccc3f070f7c97e35c68767aea9926d412a9cf22b8e7adef060818f2`
- size bytes: `69006`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 6`
  - `canonical_ledger_len 6`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 4`
  - `evidence_tokens_len 8`
  - `interaction_counts_len 5`
  - `kill_log_len 6`
  - `park_set_len 9`
  - `reject_log_len 18`
  - `sim_promotion_status_len 14`
  - `sim_registry_len 14`
  - `sim_results_len 8`
  - `survivor_ledger_len 38`
  - `survivor_order_len 38`
  - `term_registry_len 4`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains four canonical evidence obligations:
    - `S000001_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE`
    - `S000002_CANON_DENSITY_MATRIX`
    - `S000003_CANON_POSITIVE`
    - `S000004_CANON_SEMIDEFINITE`
  - `kill_log` retains six kill signals with tokens:
    - `NEG_INFINITE_SET` for `S000001_*` and `S000003_*`
    - `NEG_COMMUTATIVE_ASSUMPTION` for `S000002_*`
  - `park_set` retains nine parked items with tag mix:
    - `NEAR_REDUNDANT` x `8`
    - `UNDEFINED_TERM_USE` x `1`
  - `reject_log` retains eighteen reject rows with tag mix:
    - `SCHEMA_FAIL` x `9`
    - `NEAR_REDUNDANT` x `8`
    - `UNDEFINED_TERM_USE` x `1`
  - all `14` `sim_promotion_status` entries are `PARKED`

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/sequence_state.json`
- sha256: `62918dc809aa2be8e01cdc79a197a341d00101777f998315c4d7bce19c86c8e7`
- size bytes: `91`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 7`
  - `A1 6`
  - `A2 0`
  - `B 6`
  - `SIM 8`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/a1_inbox/sequence_state.json`
- sha256: `a479ee124dafc76f07e247a85897e53e7e327e5ceb5dcab49027c8c8858ce851`
- size bytes: `34`
- source class: inbox-local A1 sequence ledger
- retained marker:
  - `RUN_QIT_AUTORATCHET_0003|A1 -> 6`
- relation to root sequence ledger:
  - root and inbox ledgers are not identical JSON shapes
  - both preserve the same terminal A1 sequence max of `6`

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/events.jsonl`
- sha256: `7bfe0d66e9fdbd0212fa06c66180d6294e6227496e3f9c90d3e044b08408769f`
- size bytes: `10706`
- line count: `7`
- source class: compact autoratchet event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `6`
  - step values present:
    - `1`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000006_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000004_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000005_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000006_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000007_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim outputs total: `8`
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

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/soak_report.md`
- sha256: `711624ab67a1fa281e0c2210a4bfb482f5fd27980129a08bbe6ffa1bc15bbc01`
- size bytes: `10892`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 3`
  - `parked_total 2`
  - `rejected_total 2`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `SCHEMA_FAIL 4`
- retained event texture:
  - the last-event window preserves six retained result rows over strategy packets `000001` through `000006`
  - the first two retained rows show `accepted 7`
  - the third retained row shows `accepted 9`, `parked 3`, `rejected 3`
  - the final two retained rows both show `accepted 3`, `parked 2`, `rejected 2`

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/zip_packets`
- source class: embedded packet lattice
- file count: `27`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `6`
  - `A1_TO_A0_STRATEGY_ZIP`: `6`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `6`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `8`
- embedded strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> a910bbac4a807847b3783fdc88b75fc1764aa386a00dad10c4381951fbaf0944`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> c987633a7916745292af638d3ffbdb3786888d0a7c22c6f5ab0d8b9d18341ae4`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 9c5d4b87afc1f9c65564c05e7d0a578760bdc39411effef5950e29f22e512cb6`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> cca04fe4ae522b8b10161b7643a2cfd2b938565cde203129b82d4eb5e789bdd9`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 2e101c8e5a0a7f388652b0f56345801b50943b3677b8a9c77fe4cf9b78880af8`
  - `000006_A1_TO_A0_STRATEGY_ZIP.zip -> 9c98991254f77d135544ad27b19409fae0b8f3c644d7f68d3f81404b64972d18`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003/a1_inbox/consumed`
- source class: fully consumed strategy residue
- file count: `6`
- consumed strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> 97093c1ef5edc8b59f23806d54d023cef830e70390de1b70f900612a90cea167`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 8d4e46c146d783fbccca57192a6acdadb50a8b9d98714651d9ec2dd8030004c9`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 28aad2cbe01858e71bbc9ba2159bbfb449da28c994abfdec2c8445a9f1d8cd9b`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> ec380b9705d33b6f1f1fdba7d63e707e5dd18e351b1297b3311307ff2a223f94`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 2775f8cd3a9e6201a08f2e90f965bc8274c0fdef5b35547bb1e6cc6ef1edeb75`
  - `000006_A1_TO_A0_STRATEGY_ZIP.zip -> ca2156370f47585d5d297e358d38048e829e6682c9a10140ccf61438e5d9ad60`
- lane relation to embedded strategy packets:
  - same six filenames appear in both consumed and embedded lanes
  - all six same-name pairs differ byte-for-byte
  - no live unconsumed strategy packets remain in `a1_inbox/`

## 3) Structural Map Of The Sources
### Segment A: queue-drained six-pass autoratchet run
- source anchors:
  - run root inventory
  - `a1_inbox/consumed/`
  - `a1_inbox/sequence_state.json`
- source role:
  - preserves a direct autoratchet run captured after six strategy packets were consumed and the inbox drained
- strong markers:
  - six consumed strategy packets survive
  - no live strategy packet files remain in `a1_inbox/`
  - no wrapper README is present

### Segment B: one-step headline over six retained passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves strong step compression where six retained result passes collapse into one nominal completed step
- strong markers:
  - `steps_completed 1`
  - `events.jsonl` keeps six result-shaped rows after the initial request row
  - all retained result rows use step value `1`

### Segment C: digest-collapse summary over multi-digest history
- source anchors:
  - `summary.json`
  - `events.jsonl`
- source role:
  - preserves a severe collapse of digest diversity in the headline summary
- strong markers:
  - summary records `unique_strategy_digest_count 1`
  - summary records both export digest counts as `1`
  - retained result rows preserve `6` distinct strategy digests, `6` export content digests, and `5` export structural digests

### Segment D: parked and rejected semantic burden under final-window counters
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves a larger parked/reject burden than the final headline window suggests
- strong markers:
  - `summary.json` ends at `parked_total 2` and `rejected_total 2`
  - `state.json` keeps `park_set_len 9`, `reject_log_len 18`, and `kill_log_len 6`
  - all `14` sim promotion statuses are `PARKED`

### Segment E: dual sequence ledgers with aligned A1 max
- source anchors:
  - root `sequence_state.json`
  - `a1_inbox/sequence_state.json`
- source role:
  - preserves both global and inbox-local views of terminal sequence state
- strong markers:
  - root ledger keeps `A1 6` alongside `A0 7`, `B 6`, and `SIM 8`
  - inbox ledger keeps only `RUN_QIT_AUTORATCHET_0003|A1 -> 6`
  - the JSON shapes differ even though the A1 max agrees

### Segment F: same-name strategy-family instability across six pairs
- source anchors:
  - `zip_packets/`
  - `a1_inbox/consumed/`
- source role:
  - preserves a full six-packet family where filename identity is never enough to recover byte identity
- strong markers:
  - same names `000001` through `000006` exist in both lanes
  - all six consumed-versus-embedded pairs diverge byte-for-byte

