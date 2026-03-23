# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_REAL_A1_001_PASS`
Batch scope: archive-only intake of `TEST_REAL_A1_001`, bounded to its run-root files, empty inbox residue, missing sequence ledger, five-packet lattice, and embedded packet payloads
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001`
  - retained run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `soak_report.md`
  - retained directories:
    - `a1_inbox/`
    - `zip_packets/`
  - packet family under `zip_packets/`:
    - `000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `TEST_REAL_A1_001` and does not reopen sibling `TEST_REAL_A1_002` or `TEST_RESUME_*` runs
  - the archive value is a compact one-step real-A1-named run with one strategy packet, one export packet, one Thread-S snapshot, and two real SIM evidence returns
  - this object is useful for demotion lineage because it is transport-clean and structurally coherent, yet still preserves final-hash drift, absent sequence state, and replay-vs-name mismatch
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001`
- source class: one-step real-A1-named run root
- retained top-level contents:
  - `a1_inbox/`
  - `events.jsonl`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets/`
- missing top-level runtime surface:
  - `sequence_state.json` not retained

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id TEST_REAL_A1_001`
  - `a1_source replay`
  - `needs_real_llm false`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 4`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 2`
  - `unresolved_promotion_blocker_count 2`
  - `stop_reason MAX_STEPS`
  - retained digest diversity:
    - `unique_strategy_digest_count 1`
    - `unique_export_content_digest_count 1`
    - `unique_export_structural_digest_count 1`
  - `final_state_hash d0f83cb5c232e7aa1887d844bab1152c18990d47a1cf75c5865868e146afc107`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/state.json`
- source class: retained final state
- compact state markers:
  - `accepted_batch_count 1`
  - `canonical_ledger_len 1`
  - `evidence_tokens_len 2`
  - `interaction_counts_len 0`
  - `kill_log_len 0`
  - `reject_log_len 0`
  - `probe_meta_len 2`
  - `sim_promotion_status_len 2`
  - `sim_registry_len 2`
  - `sim_results_len 2`
  - `spec_meta_len 2`
  - `survivor_ledger_len 4`
  - survivor statuses:
    - all `4` active
  - sim promotion states:
    - both retained entries are `PARKED`
- archive meaning:
  - state preserves one accepted batch and two retained SIM tracks without any reject or kill-log entries

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/events.jsonl`
- source class: executed event ledger
- event markers:
  - retained line count: `1`
  - only event family:
    - `step_result`
  - retained execution step:
    - `1`
  - totals across retained rows:
    - `accepted_sum 4`
    - `parked_sum 0`
    - `rejected_sum 0`
  - retained state edge:
    - `state_hash_before e3790c2ef6ff9506349dc76a5fe577e74de5fe487c9fb9d6f1501af06966bfaf`
    - `state_hash_after 6835e766f6b2d89ac67187396180a33a7c769c4f9498a82ef9d2e60b6934321d`
- archive meaning:
  - events preserve one executed step only; there is no retained step-2 or queue-continuation layer

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 1`
  - `accepted_total 4`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/a1_inbox/`
- source class: empty inbox residue
- retained contents:
  - none
- archive meaning:
  - retained A1 strategy lineage survives only in `zip_packets/`, not in an inbox or consumed lane

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/zip_packets/`
- source class: asymmetric packet lattice
- packet file count: `5`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 1`
  - `A1_TO_A0_STRATEGY_ZIP 1`
  - `B_TO_A0_STATE_UPDATE_ZIP 1`
  - `SIM_TO_A0_SIM_RESULT_ZIP 2`
- archive meaning:
  - the lattice preserves one step with one positive and one alternative SIM return, but no retained second-step proposal or sequence ledger

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: only strategy packet
- sha256: `8ad8eef463cfa31e30aecd15a75dbc1e00ca35bbb508fc37219dcd55036c7f13`
- size bytes: `1909`
- payload markers:
  - `strategy_id STRAT_000101`
  - one baseline target:
    - `S_SIM_TARGET_ALPHA_S0001`
  - one alternative:
    - `S_SIM_ALT_BETA_ALT_S0001`
  - both target families:
    - `PERTURBATION`
  - both target tiers:
    - `T1_COMPOUND`
  - both negative classes:
    - `NEG_BOUNDARY`
  - `inputs.state_hash e3790c2ef6ff9506349dc76a5fe577e74de5fe487c9fb9d6f1501af06966bfaf`
  - budget:
    - `max_items 3`
    - `max_sims 3`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- source class: export packet
- sha256: `04d696af70395ee3610f64241a62ae3a0efeca4ba30ee36cec5222ade74b1a64`
- size bytes: `1419`
- payload markers:
  - export block proposes:
    - `P_BIND_ALPHA`
    - `S_SIM_TARGET_ALPHA_S0001`
    - `P_BIND_BETA`
    - `S_SIM_ALT_BETA_ALT_S0001`
  - target:
    - `THREAD_B_ENFORCEMENT_KERNEL`

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
- source class: Thread-S snapshot packet
- sha256: `00aea2b8d806ed0990c15b40674263cef445dfa7b38461f9b951386be1d77652`
- size bytes: `1529`
- payload markers:
  - snapshot format:
    - `THREAD_S_SAVE_SNAPSHOT v2`
  - provenance:
    - `ACCEPTED_BATCH_COUNT=1`
  - evidence pending:
    - `S_SIM_ALT_BETA_ALT_S0001` requires `E_BETA_OK`
    - `S_SIM_TARGET_ALPHA_S0001` requires `E_ALPHA_OK`

### Source 12
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- source class: alternative SIM result packet
- sha256: `8a23f713020cfd769de79cd6843695df000de04a54ed9c8f19a51e0d089f1331`
- size bytes: `1382`
- payload markers:
  - `SIM_ID S_SIM_ALT_BETA_ALT_S0001`
  - `tier T1_COMPOUND`
  - `family PERTURBATION`
  - `target_class TC_BETA_STEP_0001_C01`
  - evidence signal:
    - `E_BETA_OK`
  - kill signal:
    - `NEG_NEG_BOUNDARY`

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_001/zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- source class: baseline SIM result packet
- sha256: `44000f7f617a20ba4a1b6c8fa30c81374e77201c1e6d6fc68ed46ec9c5bd6547`
- size bytes: `1387`
- payload markers:
  - `SIM_ID S_SIM_TARGET_ALPHA_S0001`
  - `tier T1_COMPOUND`
  - `family PERTURBATION`
  - `target_class TC_ALPHA_STEP_0001_C01`
  - evidence signal:
    - `E_ALPHA_OK`
  - kill signal:
    - `NEG_NEG_BOUNDARY`
