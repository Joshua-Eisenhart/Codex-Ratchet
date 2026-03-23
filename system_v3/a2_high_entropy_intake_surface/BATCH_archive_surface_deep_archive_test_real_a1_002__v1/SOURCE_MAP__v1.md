# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_REAL_A1_002_PASS`
Batch scope: archive-only intake of `TEST_REAL_A1_002`, bounded to its two-step run-core files, empty inbox residue, missing sequence ledger, symmetric eight-packet lattice, and embedded strategy/export/snapshot/SIM payloads
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002`
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
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `TEST_REAL_A1_002` and does not reopen sibling `TEST_RESUME_001`
  - the archive value is a compact two-step real-A1-named run with a balanced packet lattice, no queued continuation residue, and a visibly mixed second-step closure surface
  - this object is useful for demotion lineage because summary and soak remain fairly coherent while replay attribution, missing sequence state, schema-fail second-step residue, mixed `S0001`/`S0002` survivor lineage, and final-hash drift all remain preserved
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_RESUME_001`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002`
- source class: two-step real-A1-named run root
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id TEST_REAL_A1_002`
  - `a1_source replay`
  - `needs_real_llm false`
  - `steps_completed 2`
  - `steps_requested 2`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `sim_registry_count 3`
  - `unresolved_promotion_blocker_count 3`
  - `stop_reason MAX_STEPS`
  - retained digest diversity:
    - `unique_strategy_digest_count 2`
    - `unique_export_content_digest_count 2`
    - `unique_export_structural_digest_count 2`
  - `final_state_hash b87bc843963c6751ab515f3d7b68e139ce787a6f184c667ee9e37449ac701100`
  - promotion counts by tier:
    - `T0_ATOM fail 1 pass 0`
    - `T1_COMPOUND fail 2 pass 0`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/state.json`
- source class: retained final state
- compact state markers:
  - `accepted_batch_count 2`
  - `canonical_ledger_len 2`
  - canonical previous-state hashes:
    - step `1`: `e3790c2ef6ff9506349dc76a5fe577e74de5fe487c9fb9d6f1501af06966bfaf`
    - step `2`: `cc9ebfe459641f6c94b64c92252966139a0d86f28593baadb63df64e3b13fa0d`
  - `evidence_tokens_len 2`
  - evidence tokens:
    - `E_OMEGA_OK`
    - `E_SIGMA_OK`
  - `probe_meta_len 2`
  - `reject_log_len 1`
  - reject detail:
    - `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`
  - `sim_promotion_status_len 3`
  - sim promotion states:
    - all retained entries are `PARKED`
  - `sim_registry_len 3`
  - retained sim ids:
    - `S_SIM_ALT_OMEGA_ALT_S0001`
    - `S_SIM_ALT_OMEGA_ALT_S0002`
    - `S_SIM_TARGET_SIGMA_S0001`
  - `sim_results_len 2`
  - `survivor_ledger_len 5`
  - survivor statuses:
    - all `5` retained entries are `ACTIVE`
  - `evidence_pending_len 0`
  - `kill_log_len 0`
- archive meaning:
  - final state keeps two-step acceptance and three parked promotion states, but the retained survivor set is mixed: the `OMEGA` alternative advances to `S0002` while the `SIGMA` target remains at `S0001`

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/events.jsonl`
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
  - retained per-step edges:
    - step `1`:
      - `accepted 4`
      - `rejected 0`
      - `unresolved_promotion_blockers 2`
      - `state_hash_before e3790c2ef6ff9506349dc76a5fe577e74de5fe487c9fb9d6f1501af06966bfaf`
      - `state_hash_after 7a249c9eb801f52d0a80c0f5ea4db7e59c520470116c6bcd0c8d9fcbfb3f6f44`
    - step `2`:
      - `accepted 3`
      - `rejected 1`
      - `reject_tags SCHEMA_FAIL`
      - `unresolved_promotion_blockers 3`
      - `state_hash_before cc9ebfe459641f6c94b64c92252966139a0d86f28593baadb63df64e3b13fa0d`
      - `state_hash_after 7716a6371c13b364f94a9239ac5c5e924cf51eca3514105d9afd557aad62e567`
- archive meaning:
  - events preserve a clean two-step execution count, but the event chain does not close the full state lineage retained elsewhere

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 2`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `SCHEMA_FAIL 1`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/a1_inbox/`
- source class: empty inbox residue
- retained contents:
  - none
- archive meaning:
  - retained A1 strategy lineage survives only in `zip_packets/`; there is no queued step-3 continuation surface

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/`
- source class: symmetric two-step packet lattice
- packet file count: `8`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 2`
  - `A1_TO_A0_STRATEGY_ZIP 2`
  - `B_TO_A0_STATE_UPDATE_ZIP 2`
  - `SIM_TO_A0_SIM_RESULT_ZIP 2`
- archive meaning:
  - transport surfaces preserve two complete step lanes without any third-step continuation packet

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: first strategy packet
- sha256: `d88ce35a3496b4a68d13119e283a52f82ebf60e8f21377bb142317678148c3c5`
- size bytes: `1909`
- payload markers:
  - `strategy_id STRAT_000202`
  - one target spec:
    - `S_SIM_TARGET_SIGMA_S0001`
    - family `PERTURBATION`
    - tier `T1_COMPOUND`
    - negative class `NEG_BOUNDARY`
  - one alternative spec:
    - `S_SIM_ALT_OMEGA_ALT_S0001`
    - family `PERTURBATION`
    - tier `T1_COMPOUND`
    - negative class `NEG_BOUNDARY`
  - `inputs.state_hash e3790c2ef6ff9506349dc76a5fe577e74de5fe487c9fb9d6f1501af06966bfaf`
  - budget:
    - `max_items 5`
    - `max_sims 5`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: second strategy packet
- sha256: `f79c0d2fa50cb6d99b2f1325ce515c48799687b8692489e08e0dd8060741e77a`
- size bytes: `1906`
- payload markers:
  - `strategy_id STRAT_000202`
  - one target spec:
    - `S_SIM_TARGET_SIGMA_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - negative class empty
  - one alternative spec:
    - `S_SIM_ALT_OMEGA_ALT_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - negative class `NEG_BOUNDARY`
  - `inputs.state_hash cc9ebfe459641f6c94b64c92252966139a0d86f28593baadb63df64e3b13fa0d`
  - budget:
    - `max_items 5`
    - `max_sims 5`

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- source class: second export packet
- sha256: `5252cbaee1e1a62943f412405209830f7ea90db513a4108ebf514139e74dc8a2`
- size bytes: `1414`
- payload markers:
  - target thread:
    - `THREAD_B_ENFORCEMENT_KERNEL`
  - export targets:
    - `P_BIND_SIGMA`
    - `S_SIM_TARGET_SIGMA_S0002`
    - `P_BIND_OMEGA`
    - `S_SIM_ALT_OMEGA_ALT_S0002`
  - target negative class:
    - empty
  - alternative negative class:
    - `NEG_BOUNDARY`

### Source 12
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
- source class: second Thread-S snapshot packet
- sha256: `46e5db1dbdb0b7f386910ba1340d5d91c988f0a221deae1fea9da0fff00864b6`
- size bytes: `1575`
- payload markers:
  - snapshot format:
    - `THREAD_S_SAVE_SNAPSHOT v2`
  - survivor ledger keeps:
    - `P_BIND_OMEGA`
    - `P_BIND_SIGMA`
    - `S_SIM_ALT_OMEGA_ALT_S0001`
    - `S_SIM_ALT_OMEGA_ALT_S0002`
    - `S_SIM_TARGET_SIGMA_S0001`
  - `EVIDENCE_PENDING EMPTY`
  - provenance:
    - `ACCEPTED_BATCH_COUNT=2`

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- source class: first SIM result packet
- sha256: `0926ac1610f05866d46e2793a52b69ea1699b0baa7b563eb685bcb8785561b1c`
- size bytes: `1392`
- payload markers:
  - `sim_id S_SIM_ALT_OMEGA_ALT_S0001`
  - `tier T1_COMPOUND`
  - `family PERTURBATION`
  - `negative_class NEG_BOUNDARY`
  - evidence signal:
    - `E_OMEGA_OK`
  - kill signal:
    - `NEG_NEG_BOUNDARY`

### Source 14
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_REAL_A1_002/zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- source class: second SIM result packet
- sha256: `1d1b9087a7b8f8e6181115554aaede8b0247bbe5ddfc1e6200a3f2b17d514574`
- size bytes: `1391`
- payload markers:
  - `sim_id S_SIM_TARGET_SIGMA_S0001`
  - `tier T1_COMPOUND`
  - `family PERTURBATION`
  - `negative_class NEG_BOUNDARY`
  - evidence signal:
    - `E_SIGMA_OK`
  - kill signal:
    - `NEG_NEG_BOUNDARY`
