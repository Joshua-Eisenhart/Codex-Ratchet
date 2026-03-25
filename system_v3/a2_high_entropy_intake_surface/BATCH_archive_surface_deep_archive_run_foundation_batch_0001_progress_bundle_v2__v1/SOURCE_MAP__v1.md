# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle_v2__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_PROGRESS_BUNDLE_V2_PASS`
Batch scope: archive-only intake of `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`, bounded to the patch README, embedded run snapshot, and carried strategy-packet surfaces
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/README_PATCH_AND_RUN.txt`
  - embedded child run:
    - `RUN_FOUNDATION_BATCH_0001/summary.json`
    - `RUN_FOUNDATION_BATCH_0001/state.json`
    - `RUN_FOUNDATION_BATCH_0001/state.json.sha256`
    - `RUN_FOUNDATION_BATCH_0001/sequence_state.json`
    - `RUN_FOUNDATION_BATCH_0001/events.jsonl`
    - `RUN_FOUNDATION_BATCH_0001/soak_report.md`
    - `RUN_FOUNDATION_BATCH_0001/zip_packets/`
    - `RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed/`
  - carried packet lane:
    - `packets/`
- reason for bounded family batch:
  - this pass processes only the v2 progress-bundle derivative and does not reopen sibling bundles or the parent run
  - the bundle is a patched replay/export surface rather than a full runnable archive root
  - the archive value is the patch-lineage framing, the retained two-step continuation snapshot, and the split between clean continuation claims and residual historical failure state
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_bundle`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`
- source class: progress-bundle-v2 root
- total files: `90`
- total directories: `5`
- top-level entries:
  - `README_PATCH_AND_RUN.txt`
  - `RUN_FOUNDATION_BATCH_0001`
  - `packets`

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/README_PATCH_AND_RUN.txt`
- sha256: `d56c60d75a5200d40441de946c4bf14dbe58e7a30d4a082cc3d53a7199042bfd`
- size bytes: `649`
- source class: patch-and-run README
- key markers:
  - runtime patches:
    - `packet mode no longer propagates prior reject tags into compile_export_block`
    - `packet mode no longer halts on A2_OPERATOR_SET_EXHAUSTED`
    - `resume now prefers run-local state/sequence files`
    - `resume backfills per-source sequence maxima from run zip_packets when sequence_state is missing`
  - current run:
    - `RUN_ID RUN_FOUNDATION_BATCH_0001`
    - `final_state_hash 84ce3614ca18f463e467df8d7617e0540911e581ae16c74b50baf85ae01824ac`
    - `term_registry_count 26`
    - `sim_registry_count 35`
    - `kill_log_count 7`
    - `canonical_ledger_len 7`
  - latest clean continuation:
    - packet set `000010 + 000011` accepted with no rejects or parks in a `2`-step run

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001`
- source class: embedded child run snapshot
- files: `78`
- directories: `3`
- top-level entries:
  - `a1_inbox`
  - `events.jsonl`
  - `sequence_state.json`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets`
- notable absences inside embedded run:
  - no `HARDMODE_METRICS.json`
  - no `sim/` directory

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/summary.json`
- sha256: `82fac56727650ee5079b3fd43595a397bd3d642ba260b9b3c5364f5d5eb13fc3`
- size bytes: `835`
- source class: embedded final snapshot summary
- summary markers:
  - `steps_completed 2`
  - `accepted_total 29`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 35`
  - `unresolved_promotion_blocker_count 7`
  - `unique_strategy_digest_count 2`
  - `final_state_hash 84ce3614ca18f463e467df8d7617e0540911e581ae16c74b50baf85ae01824ac`

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/state.json`
- sha256: `84ce3614ca18f463e467df8d7617e0540911e581ae16c74b50baf85ae01824ac`
- size bytes: `118593`
- source class: embedded final snapshot state
- compact state markers:
  - `accepted_batch_count 7`
  - `canonical_ledger_len 7`
  - `survivor_order_len 95`
  - `term_registry_len 26`
  - `kill_log_len 7`
  - `park_set_len 7`
  - `reject_log_len 11`
  - `sim_registry_len 35`
  - `sim_results_len 35`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained historical residue markers:
  - `park_set` contains seven parked symbolic terms even though the embedded summary reports `parked_total 0`
  - `reject_log` retains eleven schema-failure records even though the embedded summary reports `rejected_total 0`
  - `kill_log` records seven `NEG_NEG_COMMUTATIVE_ASSUMPTION` kill signals across the preserved SIM ladder

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/state.json.sha256`
- source class: embedded state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches the README final state hash
  - declared hash matches the summary final state hash

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/sequence_state.json`
- sha256: `34868de887264b57fd2d456be2cb5e3197ea283bf88667c6976b1ca660b73941`
- size bytes: `93`
- source class: restored sequence ledger
- sequence maxima:
  - `A0 9`
  - `A1 9`
  - `A2 0`
  - `B 7`
  - `SIM 35`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/events.jsonl`
- sha256: `e3ee53b9c2ed4abf5d38513899afd371af86738871603325d2c7f821fbe82d79`
- size bytes: `23407`
- line count: `9`
- source class: compact embedded event ledger
- event markers:
  - event kinds:
    - `a1_strategy_request_emitted`: `2`
    - `step_result`: `7`
  - step values present:
    - `1`
    - `2`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000007_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000008_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000009_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000004_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000005_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000006_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000008_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000009_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim result packet count: `35`
  - persistent path drift:
    - event rows still point to runtime-path `sim/sim_evidence_*` files that are not retained inside the bundle

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/soak_report.md`
- sha256: `2020c990cb59edbf22cb0a1b532ee34bbe88e287ae916c5c68ef18aaf8a0d2c9`
- size bytes: `23598`
- source class: embedded human-readable soak report
- report markers:
  - `cycle_count 2`
  - `accepted_total 29`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tag: `SCHEMA_FAIL 2`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/zip_packets`
- source class: embedded packet subset
- file count: `61`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `2`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `8`
  - `A1_TO_A0_STRATEGY_ZIP`: `9`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `7`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `35`

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/packets`
- source class: carried strategy packets
- file count: `11`
- packet kind counts:
  - `A1_TO_A0_STRATEGY_ZIP`: `11`
- strongest marker:
  - packet carry includes `000010` and `000011`, which the README names as the latest clean continuation set

### Source 12
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2/RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed`
- source class: embedded consumed strategy residue
- file count: `11`
- exact-copy relation:
  - names and hashes are byte-identical to `packets/`

## 3) Structural Map Of The Sources
### Segment A: patch-and-run triad
- source anchors:
  - bundle root inventory
- source role:
  - defines the bundle as three coordinated surfaces rather than a single run directory
- strong markers:
  - operator-facing patch note: `README_PATCH_AND_RUN.txt`
  - embedded patched child snapshot: `RUN_FOUNDATION_BATCH_0001/`
  - external carried strategy lane: `packets/`

### Segment B: patched continuation claim surface
- source anchors:
  - source 2
- source role:
  - preserves the archive operator narrative that v2 is a patched continuation rather than a plain replay bundle
- strong markers:
  - README is centered on runtime patch semantics, not replay procedure
  - resume behavior is explicitly redirected toward run-local `state.json` and `sequence_state.json`
  - latest clean continuation is declared against packet set `000010 + 000011`

### Segment C: embedded two-step snapshot surface
- source anchors:
  - sources 4-7 and 9
- source role:
  - preserves the retained final child-run snapshot after the v2 continuation
- strong markers:
  - summary, README, state hash sidecar, and `state.json` all agree on final hash `84ce3614...`
  - embedded summary compresses the run to `steps_completed 2`, `accepted_total 29`, and `sim_registry_count 35`
  - restored `sequence_state.json` is a new control surface inside the embedded run and anchors sequence maxima by source

### Segment D: clean-step versus dirty-state split
- source anchors:
  - sources 4, 5, and 9
- source role:
  - preserves the contradiction between step-local clean continuation and bundle-level retained historical residue
- strong markers:
  - summary and soak report say `parked_total 0` and `rejected_total 0`
  - state still retains `park_set_len 7` and `reject_log_len 11`
  - summary reports `unresolved_promotion_blocker_count 7` while `kill_log_len 7` remains the only clearly retained blocker-like ladder inside state

### Segment E: event-ledger undercapture surface
- source anchors:
  - source 8
- source role:
  - preserves only a narrow trace of the patched continuation rather than a full packet-history proof
- strong markers:
  - total event lines: `9`
  - event ledger references strategy packets through `000009`
  - README names `000010 + 000011` as the latest clean continuation set, but those packets are not referenced in `events.jsonl`

### Segment F: duplicated packet carry surface
- source anchors:
  - sources 10-12
- source role:
  - preserves the transport residue and carried strategy lane as separate but overlapping archive surfaces
- strong markers:
  - embedded `zip_packets/` keeps a mixed packet lattice of `61` files
  - top-level `packets/` keeps `11` strategy zips only
  - `packets/` and `a1_inbox/consumed/` are byte-identical duplicates

