# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_BUNDLE_PASS`
Batch scope: archive-only intake of `RUN_FOUNDATION_BATCH_0001_bundle`, bounded to the working-run README, two detached top-level strategy packets, and the embedded child run snapshot
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/README_WORKING_RUN.txt`
  - detached top-level strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - embedded child run:
    - `RUN_FOUNDATION_BATCH_0001/summary.json`
    - `RUN_FOUNDATION_BATCH_0001/state.json`
    - `RUN_FOUNDATION_BATCH_0001/state.json.sha256`
    - `RUN_FOUNDATION_BATCH_0001/events.jsonl`
    - `RUN_FOUNDATION_BATCH_0001/soak_report.md`
    - `RUN_FOUNDATION_BATCH_0001/zip_packets/`
    - `RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the early `RUN_FOUNDATION_BATCH_0001_bundle` object and does not reopen sibling bundles or later runs
  - the bundle is a compact operator working-run kit rather than a full parent-run export
  - the archive value is the direct operator recipe, the clean two-step compact snapshot, and the packet-name collision preserved inside the bundle itself
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle`
- source class: working-run bundle root
- total files: `27`
- total directories: `4`
- top-level entries:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `README_WORKING_RUN.txt`
  - `RUN_FOUNDATION_BATCH_0001`

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/README_WORKING_RUN.txt`
- sha256: `b7e84797fe28e48cfe355537fba9985a0e460ddfa628bab18ff6c820fcc0272d`
- size bytes: `585`
- source class: working-run README
- key markers:
  - `RUN_ID RUN_FOUNDATION_BATCH_0001`
  - execution mode: `packet`
  - command ladder:
    - clean bootstrap run with `--steps 1 --clean`
    - place two `A1_TO_A0_STRATEGY_ZIP` packets into `a1_inbox/`
    - continue with `--steps 2`
  - expected summary highlights:
    - `accepted_total 30`
    - `rejected_total 0`
    - `parked_total 0`
    - `kill_log_count 2`
    - `sim_registry_count 10`
    - `final_state_hash e2037bacdeaaa3425f00f8d00880127228f4a372457e8ae9ccf62a9b2b993ddc`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: detached top-level strategy packet
- size bytes: `2458`
- sha256: `cda70b1eed0e8f9f307a4f1f987c70fd94be7e432529acb5bed46308cf140bd0`

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/000002_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: detached top-level strategy packet
- size bytes: `2390`
- sha256: `833b223e74ccb4358b1c97dcfca39a87a7db365287b9802e5b93caccb80871c2`

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001`
- source class: embedded child run snapshot
- files: `24`
- directories: `3`
- top-level entries:
  - `a1_inbox`
  - `events.jsonl`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets`
- notable absences inside embedded run:
  - no `HARDMODE_METRICS.json`
  - no `sequence_state.json`
  - no `sim/` directory

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/summary.json`
- sha256: `9b38904a26ebb4ae870f54d6a26057b56af9c76a50dcdbf4c929d355bc21dc62`
- size bytes: `834`
- source class: embedded final snapshot summary
- summary markers:
  - `steps_completed 2`
  - `accepted_total 30`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 10`
  - `unresolved_promotion_blocker_count 2`
  - `kill-log-compatible tier result`: `T1_COMPOUND fail 2 pass 4`
  - `final_state_hash e2037bacdeaaa3425f00f8d00880127228f4a372457e8ae9ccf62a9b2b993ddc`

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/state.json`
- sha256: `e2037bacdeaaa3425f00f8d00880127228f4a372457e8ae9ccf62a9b2b993ddc`
- size bytes: `36097`
- source class: embedded final snapshot state
- compact state markers:
  - `accepted_batch_count 2`
  - `canonical_ledger_len 2`
  - `survivor_order_len 32`
  - `term_registry_len 10`
  - `kill_log_len 2`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_registry_len 10`
  - `sim_results_len 10`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained clean-state markers:
  - no parked terms
  - no reject-log entries
  - two kill signals retained for `NEG_NEG_COMMUTATIVE_ASSUMPTION`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/state.json.sha256`
- source class: embedded state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches the README final state hash
  - declared hash matches the summary final state hash

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/events.jsonl`
- sha256: `c05d8c74fabc4c26196c55d59a9b5ba7d74f26578a6a3198c606f105603795ab`
- size bytes: `6826`
- line count: `3`
- source class: compact embedded event ledger
- event markers:
  - event kinds:
    - `a1_strategy_request_emitted`: `1`
    - `step_result`: `2`
  - step values present:
    - `1`
    - `2`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim result packet count: `10`
  - persistent path drift:
    - event rows still point to runtime-path `sim/sim_evidence_*` files that are not retained inside the bundle

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/soak_report.md`
- sha256: `ebb2ef89b67642c44c9d24bf3e7e47e9de439f77ef4cc4c074e70f5667b2fa31`
- size bytes: `6995`
- source class: embedded human-readable soak report
- report markers:
  - `cycle_count 2`
  - `accepted_total 30`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tag set: `NONE`

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/zip_packets`
- source class: embedded packet subset
- file count: `17`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `2`
  - `A1_TO_A0_STRATEGY_ZIP`: `2`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `2`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `10`
- preserved packet-name split:
  - embedded `000001_A1_TO_A0_STRATEGY_ZIP.zip` matches the detached top-level packet byte-for-byte
  - embedded `000002_A1_TO_A0_STRATEGY_ZIP.zip` has different bytes and hash `573d01fa8bcbd01920d32666644eea6f59ad68373ac861719338044ba127a276` despite sharing the same filename as the detached top-level packet

### Source 12
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle/RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed`
- source class: embedded consumed strategy residue
- file count: `2`
- exact-copy relation:
  - names and hashes are byte-identical to the two detached top-level strategy packets

## 3) Structural Map Of The Sources
### Segment A: working-run instruction surface
- source anchors:
  - bundle root inventory
  - `README_WORKING_RUN.txt`
- source role:
  - preserves a direct operator recipe for reproducing a small packet-driven continuation
- strong markers:
  - explicit three-step command ladder
  - expected summary targets written in advance
  - detached strategy packets placed at bundle root rather than under a dedicated `packets/` directory

### Segment B: compact clean snapshot surface
- source anchors:
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
  - `soak_report.md`
- source role:
  - preserves a very small two-step final snapshot with strong hash consistency
- strong markers:
  - README, summary, state, and sidecar all agree on final hash `e2037bac...`
  - clean-state counters hold at zero for parked and rejected totals
  - state remains small: `term_registry_len 10`, `sim_registry_len 10`

### Segment C: narrow event and packet proof surface
- source anchors:
  - `events.jsonl`
  - `zip_packets/`
- source role:
  - preserves only the minimal transport ladder needed to show two strategy-driven steps
- strong markers:
  - event ledger contains only `3` lines
  - packet lattice contains only `17` packet files
  - export packets stop at `000003`, strategy packets stop at `000002`, and sim results stop at `000010`

### Segment D: detached input-lane residue surface
- source anchors:
  - top-level `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - top-level `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/`
- source role:
  - preserves the two operator-supplied strategy packets outside the embedded run root
- strong markers:
  - detached top-level packets are duplicated exactly in `a1_inbox/consumed/`
  - the bundle therefore keeps both operator input residue and child-run residue for the same two strategy packet names

### Segment E: packet-name collision surface
- source anchors:
  - top-level detached packets
  - embedded `zip_packets/`
- source role:
  - preserves an internal archive contradiction on what `000002_A1_TO_A0_STRATEGY_ZIP.zip` actually is
- strong markers:
  - detached `000002_A1_TO_A0_STRATEGY_ZIP.zip` hash is `833b223e...`
  - embedded `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip` hash is `573d01fa...`
  - same filename, different bytes, no bundled explanation

