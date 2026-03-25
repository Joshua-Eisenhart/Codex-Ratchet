# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_PROGRESS_BUNDLE_PASS`
Batch scope: archive-only intake of `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`, bounded to the replay README, embedded run snapshot, and carried packet surfaces
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/README_PROGRESS.txt`
  - embedded child run:
    - `RUN_FOUNDATION_BATCH_0001/summary.json`
    - `RUN_FOUNDATION_BATCH_0001/state.json`
    - `RUN_FOUNDATION_BATCH_0001/state.json.sha256`
    - `RUN_FOUNDATION_BATCH_0001/events.jsonl`
    - `RUN_FOUNDATION_BATCH_0001/soak_report.md`
    - `RUN_FOUNDATION_BATCH_0001/zip_packets/`
    - `RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed/`
  - carried replay packets:
    - `packets/`
- reason for bounded family batch:
  - the previous batch processed the full parent run; this pass processes only its derived `PROGRESS_BUNDLE`
  - the bundle is structurally different from the parent run and should be treated as a replay/export surface, not as a smaller equivalent copy
  - this preserves early-foundation subset lineage and replay semantics without reopening sibling bundles or the full parent run again
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`
- source class: progress-bundle root
- total files: `63`
- total directories: `5`
- top-level entries:
  - `README_PROGRESS.txt`
  - `RUN_FOUNDATION_BATCH_0001`
  - `packets`

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/README_PROGRESS.txt`
- sha256: `0fed33003713553d338f011668f49c888e8c2c6314a0d86954b9e58f83ffabd5`
- size bytes: `982`
- source class: replay README
- key markers:
  - `RUN_ID RUN_FOUNDATION_BATCH_0001`
  - `Mode packet (no ollama, no openrouter)`
  - staged execution over clean bootstrap plus injected packet sets through `000007`
  - current final state hash: `0e013eb1b87429686cf1b588fa2a7e45455cb145765ad63a5fdfa3c1eed49be8`
  - cumulative observed from events: `accepted 64`, `parked 7`, `rejected 4`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001`
- source class: embedded child run snapshot
- files: `55`
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

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/summary.json`
- sha256: `236f5d553acc51f5d058a7b4ba2a03bc18c9bedea69bd7f3e30a277325cd0645`
- size bytes: `835`
- source class: embedded final snapshot summary
- summary markers:
  - `steps_completed 1`
  - `accepted_total 15`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 25`
  - `unresolved_promotion_blocker_count 5`
  - `final_state_hash 0e013eb1b87429686cf1b588fa2a7e45455cb145765ad63a5fdfa3c1eed49be8`

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/state.json`
- sha256: `0e013eb1b87429686cf1b588fa2a7e45455cb145765ad63a5fdfa3c1eed49be8`
- size bytes: `85352`
- source class: embedded final snapshot state
- compact state markers:
  - `accepted_batch_count 5`
  - `canonical_ledger_len 5`
  - `survivor_order_len 66`
  - `term_registry_len 18`
  - `kill_log_len 5`
  - `park_set_len 7`
  - `reject_log_len 11`
  - `sim_registry_len 25`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/state.json.sha256`
- source class: embedded state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256 and the README current final state hash

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/events.jsonl`
- sha256: `6688695c2bd75762ca96790707d29ca8c57cbb4e55015d3d0b4539a75df95ee0`
- size bytes: `16561`
- line count: `6`
- source class: compact embedded event ledger
- referenced strategy packets:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000007_A1_TO_A0_STRATEGY_ZIP.zip`
- referenced export packets:
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000004_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000005_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000006_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- referenced sim result packet count: `25`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/soak_report.md`
- sha256: `7fcacf3bfbbde39ae53155497e59126fbeb544f9aabe03a5cd89e7212c1bbd23`
- size bytes: `16746`
- source class: embedded human-readable report
- report markers:
  - `cycle_count 1`
  - `accepted_total 15`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tag: `SCHEMA_FAIL 2`

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/zip_packets`
- source class: embedded packet subset
- file count: `43`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `5`
  - `A1_TO_A0_STRATEGY_ZIP`: `7`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `5`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `25`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/packets`
- source class: carried replay strategy packets
- file count: `7`
- packet kind counts:
  - `A1_TO_A0_STRATEGY_ZIP`: `7`

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE/RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed`
- source class: embedded consumed strategy residue
- file count: `7`
- exact-copy relation:
  - names and hashes are byte-identical to `packets/`

## 3) Structural Map Of The Sources
### Segment A: progress-bundle triad
- source anchors:
  - bundle root inventory
- source role:
  - defines the bundle as three coordinated surfaces rather than one run directory
- strong markers:
  - operator-facing replay note: `README_PROGRESS.txt`
  - embedded child snapshot: `RUN_FOUNDATION_BATCH_0001/`
  - external carried strategy lane: `packets/`

### Segment B: replay README surface
- source anchors:
  - source 2
- source role:
  - preserves the operator narrative of how the bundle should be replayed
- strong markers:
  - explicit staged sequence across clean bootstrap plus injected packet sets through `000007`
  - replay mode is packet-only, with no model-provider dependency
  - README reports cumulative accepted/parked/rejected totals rather than only the final one-step snapshot
  - deterministic issue notes preserve exact failure modes around flow compounds, left/right compounds, and `A2_OPERATOR_SET_EXHAUSTED`

### Segment C: embedded one-step snapshot surface
- source anchors:
  - sources 4-6 and 8
- source role:
  - preserves the terminal embedded snapshot that the bundle chose to keep
- strong markers:
  - summary, soak report, state hash sidecar, and README final hash all agree on the end-state hash `0e013eb1...`
  - embedded summary compresses the retained run to `steps_completed 1`, `accepted_total 15`, `sim_registry_count 25`, `unresolved_promotion_blocker_count 5`
  - state retains failure texture that the summary does not: `kill_log_len 5`, `park_set_len 7`, `reject_log_len 11`

### Segment D: compact event-ledger surface
- source anchors:
  - source 7
- source role:
  - preserves only a short trace of the replay sequence
- strong markers:
  - total event lines: `6`
  - one initial `a1_strategy_request_emitted` row plus five result rows
  - result rows reference only five of the seven carried strategy packets
  - all event rows still point to runtime-path `sim/sim_evidence_*` files that are not retained inside the bundle

### Segment E: packet-subset surface
- source anchors:
  - source 9
- source role:
  - preserves the mixed transport subset that the embedded run snapshot retained
- strong markers:
  - embedded packet lattice contains exactly `43` files
  - one save point, five B exports, five B updates, seven A1 strategies, and twenty-five SIM results
  - the embedded run therefore preserves only a very early packet prefix, not a broad transport ladder

### Segment F: duplicated strategy-carry surface
- source anchors:
  - sources 10-11
- source role:
  - preserves a second and third copy of the carried strategy set outside the mixed packet subset
- strong markers:
  - `packets/` has `7` strategy zips
  - `a1_inbox/consumed/` has `7` strategy zips
  - those two strategy surfaces are byte-identical

### Segment G: omission surface
- source anchors:
  - embedded run inventory
  - event/README references
- source role:
  - records what a progress bundle chose not to retain
- strong markers:
  - embedded run contains no `HARDMODE_METRICS.json`
  - embedded run contains no `sequence_state.json`
  - embedded run contains no `sim/` directory even though README and event rows reference `sim/sim_evidence_*` runtime paths

## 4) Source-Class Read
- best classification:
  - archive-only replay/export bundle for an early `RUN_FOUNDATION_BATCH_0001` subset
- useful as:
  - lineage evidence for how the historical system packaged replayable progress rather than full campaign state
  - compact map of the split between cumulative operator notes and final embedded snapshot state
  - parent/derivative comparison anchor for later progress-bundle-v2 intake
- not best classified as:
  - a faithful miniature of the full parent run
  - complete sim evidence retention
  - current runtime authority
- possible downstream consequence:
  - the next bounded pass should process `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2` to see which contradictions were tightened or widened in the second progress export
