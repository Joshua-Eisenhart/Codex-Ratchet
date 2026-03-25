# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_det_b__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_DET_B_PASS`
Batch scope: archive-only intake of `TEST_DET_B`, bounded to its run-root files, empty inbox residue, empty `a1_strategies 2/` residue, nine-packet lattice, and queued third A1 strategy packet
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B`
  - retained run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
  - retained directories:
    - `a1_inbox/`
    - `a1_strategies 2/`
    - `zip_packets/`
  - packet family under `zip_packets/`:
    - `000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `TEST_DET_B` and does not reopen sibling `TEST_REAL_A1_*` or `TEST_RESUME_*` runs
  - the archive value is a relatively coherent replay-authored two-step run with a queued third A1 continuation packet and a small packaging-residue seam
  - this object is useful for demotion lineage because executed events, soak, and summary largely agree while the packet lattice and sequence ledger preserve one extra A1 continuation beyond the executed event spine
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B`
- source class: compact deterministic-test run root
- retained top-level contents:
  - `a1_inbox/`
  - `a1_strategies 2/`
  - `events.jsonl`
  - `sequence_state.json`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets/`

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id TEST_DET_B`
  - `a1_source replay`
  - `needs_real_llm true`
  - `steps_completed 3`
  - `steps_requested 5`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `sim_registry_count 3`
  - `unresolved_promotion_blocker_count 3`
  - `stop_reason A2_OPERATOR_SET_EXHAUSTED`
  - escalation reasons:
    - `OPERATOR_SET_EXHAUSTED:SCHEMA_FAIL`
  - retained digest diversity:
    - `unique_strategy_digest_count 3`
    - `unique_export_content_digest_count 3`
    - `unique_export_structural_digest_count 3`
  - `final_state_hash 3ce0407fab9f620d58362b73726db57ff29d25efdd200b7e48d8d68e9852fd65`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/state.json`
- source class: retained final state
- compact state markers:
  - `accepted_batch_count 2`
  - `canonical_ledger_len 2`
  - canonical ledger steps:
    - `1`
    - `2`
  - canonical ledger sequences:
    - `1`
    - `2`
  - `evidence_tokens_len 2`
  - `interaction_counts_len 2`
  - `kill_log_len 0`
  - `reject_log_len 1`
  - `probe_meta_len 2`
  - `sim_promotion_status_len 3`
  - `sim_registry_len 3`
  - `sim_results_len 2`
  - `spec_meta_len 3`
  - `survivor_ledger_len 7`
  - survivor statuses:
    - all `7` active
  - reject markers:
    - `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`
- archive meaning:
  - state preserves two executed steps and one fail-closed reject, but not a third executed canonical step

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/sequence_state.json`
- source class: retained sequence ledger
- sequence maxima:
  - `A0 2`
  - `A1 3`
  - `A2 0`
  - `B 2`
  - `SIM 2`
- archive meaning:
  - the sequence surface preserves a queued third A1 packet beyond the two fully executed packet cycles

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/events.jsonl`
- source class: executed event ledger
- event markers:
  - retained line count: `2`
  - only event family:
    - `step_result`
  - retained execution steps:
    - `1`
    - `2`
  - totals across retained rows:
    - `accepted_sum 7`
    - `parked_sum 0`
    - `rejected_sum 1`
  - retained final event hash:
    - last `state_hash_after 232c159561e591ff2213b51d332c2e766bee83bac5211b3216a4eb76040f6b54`
- archive meaning:
  - events preserve only the two executed steps, not the queued third A1 continuation

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 3`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `stop_reason A2_OPERATOR_SET_EXHAUSTED`
  - top failure tags:
    - `SCHEMA_FAIL 1`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/a1_inbox/`
- source class: empty inbox residue
- retained contents:
  - none
- archive meaning:
  - replay-authored A1 strategy lineage survives only inside `zip_packets/`, not in an inbox or consumed lane

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/a1_strategies 2/`
- source class: empty packaging residue
- retained contents:
  - none
- permissions note:
  - directory mode is more restrictive than neighboring retained directories
- archive meaning:
  - preserve as packaging noise only; not a live strategy surface

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/zip_packets/`
- source class: packet lattice
- packet file count: `9`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 2`
  - `A1_TO_A0_STRATEGY_ZIP 3`
  - `B_TO_A0_STATE_UPDATE_ZIP 2`
  - `SIM_TO_A0_SIM_RESULT_ZIP 2`
- archive meaning:
  - the lattice preserves two complete execution rounds plus one extra A1 continuation packet

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: executed step-1 strategy packet
- sha256: `c03ff1e2858d731225fddc53a3857d388f1f610cd897de39aa6a28d281b387ef`
- size bytes: `1892`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - target:
    - `S_BIND_ALPHA_S0001`
  - negative alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
  - target family:
    - `PERTURBATION`
  - target tier:
    - `T1_COMPOUND`
  - target negative class:
    - `NEG_BOUNDARY`
  - `inputs.state_hash 7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`

### Source 12
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: executed step-2 strategy packet
- sha256: `c6536fded6fb7d32b86601a19026d623a700b4243d92e9f1a6f87e7d266c36db`
- size bytes: `1891`
- payload markers:
  - target:
    - `S_BIND_ALPHA_S0002`
  - negative alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0002`
  - target family:
    - `BASELINE`
  - target tier:
    - `T0_ATOM`
  - target negative class:
    - empty / absent
  - `inputs.state_hash 63995c34d867895591e52acf86da07ea9bd6d96de0c1a0de2d9afb7039fb1000`

### Source 13
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_DET_B/zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: queued step-3 continuation packet
- sha256: `45aeeea145e20eef459b45d98a848fb29639024dd3f97fa1908759a071f142ff`
- size bytes: `1891`
- payload markers:
  - target:
    - `S_BIND_ALPHA_S0003`
  - negative alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0003`
  - target family:
    - `BOUNDARY_SWEEP`
  - target tier:
    - `T1_COMPOUND`
  - target negative class:
    - empty / absent
  - `inputs.state_hash 3ce0407fab9f620d58362b73726db57ff29d25efdd200b7e48d8d68e9852fd65`
- archive meaning:
  - this packet explains why summary and sequence surfaces preserve a third strategy digest and A1 sequence value beyond the executed event spine
