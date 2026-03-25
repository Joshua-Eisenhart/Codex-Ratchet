# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_STATE_TRANSITION_MUTATION_PASS`
Batch scope: archive-only intake of `TEST_STATE_TRANSITION_MUTATION`, bounded to its one-step executed run-core files, exact duplicate ` 2` file family, empty residue directories, and retained one-step packet payloads
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION`
  - retained primary run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `sequence_state.json`
    - `events.jsonl`
    - `soak_report.md`
  - retained duplicate-suffix file family:
    - `summary 2.json`
    - `state 2.json`
    - `state.json 2.sha256`
    - `sequence_state 2.json`
    - `events 2.jsonl`
    - `soak_report 2.md`
  - retained empty residue directories:
    - `a1_inbox/`
    - `a1_strategies 2/`
    - `outbox 2/`
    - `reports 2/`
    - `zip_packets 2/`
  - packet family under `zip_packets/`:
    - `000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `TEST_STATE_TRANSITION_MUTATION` and does not reopen sibling `V2_ZIPV2_PACKET_E2E_001`
  - the archive value is a compact one-step mutation seed with one executed strategy/export/snapshot spine, two SIM returns, final-snapshot drift above the only event row, and exact duplicate sidecar residue
  - this object is useful for demotion lineage because it preserves one-step transport cleanliness while keeping semantic promotion open, snapshot-versus-state evidence splits, runtime-path leakage, and top-level packaging duplication
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION`
- source class: one-step mutation run root
- retained top-level contents:
  - `a1_inbox/`
  - `a1_strategies 2/`
  - `events 2.jsonl`
  - `events.jsonl`
  - `outbox 2/`
  - `reports 2/`
  - `sequence_state 2.json`
  - `sequence_state.json`
  - `soak_report 2.md`
  - `soak_report.md`
  - `state 2.json`
  - `state.json`
  - `state.json 2.sha256`
  - `state.json.sha256`
  - `summary 2.json`
  - `summary.json`
  - `zip_packets 2/`
  - `zip_packets/`

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/summary.json`
- source class: primary terminal run summary
- summary markers:
  - `run_id TEST_STATE_TRANSITION_MUTATION`
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
  - `final_state_hash 63995c34d867895591e52acf86da07ea9bd6d96de0c1a0de2d9afb7039fb1000`
  - promotion counts by tier:
    - `T1_COMPOUND fail 2 pass 0`
    - all other tiers `0/0`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/state.json`
- source class: primary retained final state
- compact state markers:
  - `accepted_batch_count 1`
  - `canonical_ledger_len 1`
  - canonical previous-state hash:
    - step `1`: `7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`
  - `evidence_tokens_len 2`
  - evidence tokens:
    - `E_BIND_ALPHA`
    - `E_BIND_ALPHA_ALT`
  - `probe_meta_len 2`
  - `reject_log_len 0`
  - `sim_promotion_status_len 2`
  - sim promotion states:
    - both retained entries are `PARKED`
  - `sim_registry_len 2`
  - retained sim ids:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_S0001`
  - `sim_results_len 2`
  - `survivor_ledger_len 6`
  - retained survivor ids:
    - `F01_FINITUDE`
    - `N01_NONCOMMUTATION`
    - `P_BIND_ALPHA`
    - `P_BIND_ALPHA_ALT`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_S0001`
  - `evidence_pending_len 0`
  - `kill_log_len 0`
- archive meaning:
  - final state preserves one accepted mutation batch and both one-step SIM specs, but promotion closure remains open and final state omits pending-evidence bookkeeping

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/state.json.sha256`
- source class: primary state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/sequence_state.json`
- source class: retained sequence counters
- counter markers:
  - `A0 1`
  - `A1 1`
  - `A2 0`
  - `B 1`
  - `SIM 2`
- archive meaning:
  - sequence counters preserve a single executed strategy/export/snapshot spine plus two SIM returns and no queued continuation

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/events.jsonl`
- source class: primary executed event ledger
- event markers:
  - retained line count: `1`
  - retained row omits explicit `event` field and acts as a step-result row
  - retained execution step:
    - `1`
  - totals across retained rows:
    - `accepted 4`
    - `parked 0`
    - `rejected 0`
  - step `1` markers:
    - `accepted 4`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 2`
    - `state_hash_before 7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`
    - `state_hash_after fcb5d2fe5a693a675ab749e15acc5baeeadc412c596aa076ee32c46c718fa1ba`
    - `sim_outputs 2`
- archive meaning:
  - the executed ledger preserves one clean transition only; final closure still sits above the only visible event row

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/soak_report.md`
- source class: primary human-readable stop report
- report markers:
  - `cycle_count 1`
  - `accepted_total 4`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/{summary 2.json,state 2.json,state.json 2.sha256,sequence_state 2.json,events 2.jsonl,soak_report 2.md}`
- source class: exact duplicate packaging-residue family
- duplication result:
  - each suffixed ` 2` file is byte-identical to its unsuffixed primary counterpart
  - no additional state, event, sequence, or soak information is introduced
- archive meaning:
  - treat the suffixed family as packaging duplication, not as a separate runtime branch

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/{a1_inbox,a1_strategies 2,outbox 2,reports 2,zip_packets 2}`
- source class: empty residue directories
- retained contents:
  - none
- archive meaning:
  - these directory shells are present but empty and add no executed runtime evidence

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/zip_packets/`
- source class: one-step executed packet lattice
- packet file count: `5`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 1`
  - `A1_TO_A0_STRATEGY_ZIP 1`
  - `B_TO_A0_STATE_UPDATE_ZIP 1`
  - `SIM_TO_A0_SIM_RESULT_ZIP 2`
- archive meaning:
  - the lattice preserves a single executed loop with one strategy, one export, one snapshot, and two SIM returns, without any queued continuation packet

### Source 11
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: only strategy packet
- sha256: `c42c71ae226d9d67cc12aa5dfc14ebf8a8cbe8ffdbd83097056c7f4a890a477f`
- size bytes: `1905`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - target:
    - `S_BIND_ALPHA_S0001`
    - family `PERTURBATION`
    - tier `T1_COMPOUND`
    - negative class `NEG_BOUNDARY`
  - alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - family `PERTURBATION`
    - tier `T1_COMPOUND`
    - negative class `NEG_BOUNDARY`
  - `inputs.state_hash 7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`

### Source 12
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- source class: only export packet
- sha256: `e39f055c7aeeca650ec7ade53792fc2dc61e75542047b839ab7077a279758fa7`
- size bytes: `1423`
- payload markers:
  - target thread:
    - `THREAD_B_ENFORCEMENT_KERNEL`
  - export targets:
    - `P_BIND_ALPHA`
    - `S_BIND_ALPHA_S0001`
    - `P_BIND_ALPHA_ALT`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
  - both specs keep `NEGATIVE_CLASS NEG_BOUNDARY`
  - both specs keep `KILL_IF ... NEG_NEG_BOUNDARY`

### Source 13
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
- source class: only Thread-S snapshot packet
- sha256: `74bbff97650c8613af3e016ed49abe78d2e68f701867aaa46e3f75d58b88544a`
- size bytes: `1552`
- payload markers:
  - retained survivor ids:
    - `F01_FINITUDE`
    - `N01_NONCOMMUTATION`
    - `P_BIND_ALPHA`
    - `P_BIND_ALPHA_ALT`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_S0001`
  - `EVIDENCE_PENDING` still lists both retained specs
  - provenance:
    - `ACCEPTED_BATCH_COUNT=1`

### Source 14
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_MUTATION/zip_packets/{000001_SIM_TO_A0_SIM_RESULT_ZIP.zip,000002_SIM_TO_A0_SIM_RESULT_ZIP.zip}`
- source class: retained SIM evidence pair
- member markers:
  - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - tier `T1_COMPOUND`
    - family `PERTURBATION`
    - evidence signal `E_BIND_ALPHA_ALT`
    - no explicit kill signal line retained
  - `000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `S_BIND_ALPHA_S0001`
    - tier `T1_COMPOUND`
    - family `PERTURBATION`
    - evidence signal `E_BIND_ALPHA`
    - no explicit kill signal line retained
