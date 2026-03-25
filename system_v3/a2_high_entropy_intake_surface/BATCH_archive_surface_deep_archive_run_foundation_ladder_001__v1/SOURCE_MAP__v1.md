# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_ladder_001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_FOUNDATION_LADDER_PASS`
Batch scope: archive-only intake of `RUN_FOUNDATION_LADDER_001`, bounded to the direct run folder, its embedded run-state surfaces, and the single consumed action packet
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001`
  - embedded run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `soak_report.md`
    - `zip_packets/`
  - retained input residue:
    - `a1_inbox/consumed/000001_FND_LR_ACTION.zip`
- reason for bounded family batch:
  - this pass processes only the direct `RUN_FOUNDATION_LADDER_001` run folder and does not reopen sibling runs
  - the archive object is useful as an early minimal ladder seed rather than as a broad replay/export kit
  - the key historical value is the one-step clean run shape plus the renamed-but-byte-identical consumed action packet
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001`
- source class: direct run root
- total files: `15`
- total directories: `3`
- top-level entries:
  - `a1_inbox`
  - `events.jsonl`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets`
- notable absences:
  - no wrapper README
  - no `HARDMODE_METRICS.json`
  - no `sequence_state.json`
  - no `sim/` directory

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/summary.json`
- sha256: `ad2f17a73c55899c620a5d90c1bfd84ff9e07dc43013cedeb5968b9bd3cfccbd`
- size bytes: `833`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_FOUNDATION_LADDER_001`
  - `steps_completed 1`
  - `accepted_total 15`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 5`
  - `unresolved_promotion_blocker_count 1`
  - `final_state_hash f0f1df4bcd8c85b255a6e5836354337ff0f59d2b1833c4444fc4f2de4b0792c4`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/state.json`
- sha256: `f0f1df4bcd8c85b255a6e5836354337ff0f59d2b1833c4444fc4f2de4b0792c4`
- size bytes: `17922`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 1`
  - `canonical_ledger_len 1`
  - `survivor_order_len 17`
  - `term_registry_len 5`
  - `kill_log_len 1`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_registry_len 5`
  - `sim_results_len 5`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained negative marker:
  - one `NEG_NEG_COMMUTATIVE_ASSUMPTION` kill signal remains despite zero parked/rejected totals

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/events.jsonl`
- sha256: `18b9567d21801533b830adf78395af3600e1fdb705074825145c45733640792d`
- size bytes: `3596`
- line count: `2`
- source class: compact direct event ledger
- event markers:
  - event kinds:
    - `a1_strategy_request_emitted`: `1`
    - `step_result`: `1`
  - step values present:
    - `1`
  - referenced strategy packet:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packet:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim result packet count: `5`
  - persistent path drift:
    - event rows still point to runtime-path `sim/sim_evidence_*` files that are not retained inside the archive object

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/soak_report.md`
- sha256: `9c34cc2dfdc148ad89c4cac2eff14f3a8873b144fd21d14cae59eceefdc36285`
- size bytes: `3763`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 15`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tag set: `NONE`

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/zip_packets`
- source class: embedded packet lattice
- file count: `9`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `1`
  - `A1_TO_A0_STRATEGY_ZIP`: `1`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `1`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `5`
- strategy packet marker:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip` sha256 `752588e7286706d6b218d4eaf97af36a02b31f0ea67b02b6449cc2dca6f6583e`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_LADDER_001/a1_inbox/consumed/000001_FND_LR_ACTION.zip`
- source class: consumed input residue
- size bytes: `2473`
- sha256: `752588e7286706d6b218d4eaf97af36a02b31f0ea67b02b6449cc2dca6f6583e`
- exact-copy relation:
  - byte-identical to `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - filename lineage differs: consumed surface keeps semantic name `FND_LR_ACTION`, embedded packet surface keeps protocol name `A1_TO_A0_STRATEGY_ZIP`

## 3) Structural Map Of The Sources
### Segment A: direct ladder seed run
- source anchors:
  - direct run root inventory
- source role:
  - preserves a minimal foundational run without any outer wrapper or replay README
- strong markers:
  - one-step execution only
  - minimal packet lattice of `9` files
  - one consumed action packet retained in `a1_inbox/consumed/`

### Segment B: clean one-step snapshot
- source anchors:
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
  - `soak_report.md`
- source role:
  - preserves a small clean-state capsule with strong end-state integrity
- strong markers:
  - zero parked and rejected totals across summary, state, and soak
  - final hash agreement across summary, state, and sidecar
  - run size remains very small: `term_registry_len 5`, `sim_registry_len 5`

### Segment C: retained negative seam
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves one narrow negative lineage seam beneath the clean headline
- strong markers:
  - `unresolved_promotion_blocker_count 1`
  - `kill_log_len 1`
  - kill token `NEG_NEG_COMMUTATIVE_ASSUMPTION`
  - soak report still says top failure tags `NONE`

### Segment D: renamed input-versus-protocol packet split
- source anchors:
  - `a1_inbox/consumed/000001_FND_LR_ACTION.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source role:
  - preserves the same payload under two naming regimes
- strong markers:
  - byte-identical payloads
  - semantic action name on consumed surface
  - transport/protocol name on `zip_packets` surface

### Segment E: incomplete evidence-body preservation
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves event and packet residue but not the local sim evidence texts
- strong markers:
  - runtime-path `sim/sim_evidence_*` references remain in event and soak surfaces
  - no `sim/` directory is retained

