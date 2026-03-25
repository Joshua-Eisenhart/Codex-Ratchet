# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_migrated_run_root_registry_and_family_signatures__v1`
Extraction mode: `ARCHIVE_DEEP_MIGRATED_RUN_ROOT_REGISTRY_SIGNATURE_PASS`
Batch scope: migrated run-root subtree of `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`, bounded to topology, registry behavior, family signatures, and residue surfaces
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/_RUNS_REGISTRY.jsonl`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/_CURRENT_RUN.txt`
  - representative run families:
    - `RUN_FOUNDATION_BATCH_0001`
    - `RUN_SIGNAL_0005`
    - `TEST_DET_A`
  - residual packet spill:
    - `bootpack_b_kernel_v1__runs___RESIDUAL__TEST_A1_PACKET_ZIP/a1_inbox/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- reason for bounded family batch:
  - the prior batch fixed the deep-archive family root split; this pass descends only one level into the migrated run-root subtree
  - the subtree itself is still too large to flatten, so this batch preserves the compact registry surface, the namespace spread of run families, and a few explicit representative campaigns
  - this preserves demotion lineage and structural memory without treating any preserved run residue as active runtime law
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT`
- source class: migrated run-root subtree
- immediate subtrees:
  - `bootpack_b_kernel_v1__current_state__`: `27` files / `0` directories
  - `bootpack_b_kernel_v1__runs__`: `7772` files / `178` directories
  - `bootpack_b_kernel_v1__runs___RESIDUAL__TEST_A1_PACKET_ZIP`: `1` file / `1` directory
- subtree total: `7801` files / `182` directories

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/_RUNS_REGISTRY.jsonl`
- sha256: `7cab6aa9ac70f04d09c2d9a2e24955cf018fc59c73e2c9da1099d994449bc96a`
- size bytes: `7771`
- line count: `27`
- unique run ids: `9`
- source class: compact migrated-run registry ledger

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/_CURRENT_RUN.txt`
- sha256: `26c2fb9c3eaf571f28c4aa6b148e034160319dc38f494cebe1ab637898aa165d`
- size bytes: `30`
- current pointer: `TEST_STATE_TRANSITION_CHAIN_B`
- source class: preserved current-run pointer residue

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/summary.json`
- sha256: `b6ed6a42f325bfcdce6a0ba9ce5cdab845fb617ee5f15bba2b23f59e9947516c`
- size bytes: `852`
- source class: representative long-run foundation campaign summary

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0005/summary.json`
- sha256: `cf4f00bb80097753b1c2cfc73eb4bb58a4633e03046ae56b6b50a179049c858e`
- size bytes: `838`
- source class: representative signal-family campaign summary

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_A/summary.json`
- sha256: `cdcc4e11036b6c31f76569e181aaa527108946034b63da7d25c32cd23b433dc8`
- size bytes: `868`
- source class: representative deterministic-test summary

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs___RESIDUAL__TEST_A1_PACKET_ZIP/a1_inbox/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- sha256: `b912f7b97a89a34964a513afe9ad54a94315fdc58524a470dddcaa58b856ddf0`
- size bytes: `1491`
- source class: detached residual packet artifact

## 3) Structural Map Of The Sources
### Segment A: migrated run-root split
- source anchors:
  - source 1 subtree inventory
- source role:
  - shows the migrated subtree itself is split across run history, preserved current-state residue, and one detached residual packet lane
- strong markers:
  - `bootpack_b_kernel_v1__runs__` dominates with `7772` files / `178` directories
  - `bootpack_b_kernel_v1__current_state__` is smaller but still preserved as `27` explicit residue files
  - the residual subtree contains a detached `A1_TO_A0` strategy packet outside the main run tree

### Segment B: current-state residue ladder
- source anchors:
  - source 1 current-state file listing
- source role:
  - preserves quasi-live numbered state ladders even though this whole family is now archival
- strong markers:
  - unnumbered anchors: `state.json`, `sequence_state.json`
  - numbered ladder: `state 2.json` through `state 13.json`
  - numbered ladder: `sequence_state 2.json` through `sequence_state 14.json`
  - the sequence ladder runs one step farther than the state ladder

### Segment C: registry repetition surface
- source anchors:
  - source 2 registry
- source role:
  - provides the main compact intake window into the run corpus, while also exposing that the registry is repetitive and partial rather than a unique one-row-per-run ledger
- strong markers:
  - `27` lines over only `9` unique run ids
  - each visible run id appears exactly `3` times
  - stop-reason counts:
    - `A2_OPERATOR_SET_EXHAUSTED`: `12`
    - `MAX_STEPS`: `10`
    - `A1_NEEDS_EXTERNAL_STRATEGY`: `5`
  - only `6` distinct final-state hashes are preserved across those `27` lines

### Segment D: run-family namespace taxonomy
- source anchors:
  - top-level run-directory names inside `bootpack_b_kernel_v1__runs__`
- source role:
  - shows the run tree is a mixed campaign corpus rather than one homogeneous pipeline
- strong markers:
  - top-level family counts by name prefix:
    - `RUN`: `24`
    - `TEST`: `10`
    - `V2`: `3`
    - `BOOT`: `2`
    - `GPT`: `2`
    - `PHASEA`: `1`
    - `CODEX`: `1`
  - one file-only bundle artifact also sits at the root of the run tree: `RUN_SIGNAL_0005_bundle.zip`

### Segment E: representative long-run family signatures
- source anchors:
  - sources 4-6
  - representative directory listings for `RUN_FOUNDATION_BATCH_0001` and `RUN_SIGNAL_0005`
- source role:
  - preserves explicit campaign signatures without reopening every run family
- strong markers:
  - `RUN_FOUNDATION_BATCH_0001`:
    - `2639` files / `3` directories
    - preserves `HARDMODE_METRICS.json`, `events.jsonl`, `soak_report.md`, `state.json`, `summary.json`, and a large `zip_packets/` exchange ladder
    - summary shows `steps_completed 60`, `accepted_total 840`, `sim_registry_count 1571`, `stop_reason MAX_STEPS`, `master_sim_status NOT_READY`, `unresolved_promotion_blocker_count 519`
  - `RUN_SIGNAL_0005`:
    - `609` files / `3` directories
    - preserves `SIGNAL_AUDIT.json`, `REPLAY_AUDIT.json`, core run files, and the same broad `zip_packets/` exchange skeleton
    - summary shows `steps_completed 60`, `accepted_total 960`, `sim_registry_count 360`, `stop_reason MAX_STEPS`, `master_sim_status NOT_READY`, `unresolved_promotion_blocker_count 360`
  - `TEST_DET_A`:
    - summary shows `steps_completed 3`, `accepted_total 7`, `rejected_total 1`, `sim_registry_count 3`, `stop_reason A2_OPERATOR_SET_EXHAUSTED`, `needs_real_llm true`

### Segment F: bundle-and-progress spill
- source anchors:
  - run-tree file counts
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`
  - `RUN_SIGNAL_0005_bundle.zip`
- source role:
  - records that the run tree retains both canonical-looking run directories and exported progress/bundle derivatives
- strong markers:
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`: `63` files / `5` directories
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`: `90` files / `5` directories
  - `RUN_FOUNDATION_BATCH_0001_bundle`: `27` files / `4` directories
  - `RUN_SIGNAL_0005_bundle.zip`: `5008299` bytes

### Segment G: detached residual packet spill
- source anchors:
  - source 7
- source role:
  - preserves evidence that not all packet traffic remained inside the normalized run tree
- strong markers:
  - residual subtree contains only one packet
  - packet kind is `A1_TO_A0_STRATEGY_ZIP`
  - this is linked to `TEST_A1_PACKET_ZIP`, reinforcing the archive’s external-strategy and packet-boundary history

## 4) Source-Class Read
- best classification:
  - archive-only migrated run-root topology batch for registry behavior, family signatures, and preserved run/state residue
- useful as:
  - historical map of how bootpack-b-kernel run campaigns were retained after migration
  - demotion-lineage evidence for deterministic tests, signal campaigns, foundation campaigns, and packet/bundle spill
  - bounded guide for choosing the next deep-archive descent target
- not best classified as:
  - active runtime state
  - a trustworthy current-run pointer
  - a complete ledger of every historical run outcome
- possible downstream consequence:
  - the next bounded pass should focus on `RUN_FOUNDATION_BATCH_0001` because it is both one of the largest retained families and a clear structural parent for the progress-bundle derivatives
