# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
Extraction mode: `ARCHIVE_DEEP_TEST_STATE_TRANSITION_CHAIN_A_PASS`
Batch scope: archive-only intake of `TEST_STATE_TRANSITION_CHAIN_A`, bounded to its two-step executed run-core files, queued third A1 strategy packet, exact duplicate ` 3` file family, empty residue directories, and retained packet payloads
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A`
  - retained primary run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `sequence_state.json`
    - `events.jsonl`
    - `soak_report.md`
  - retained duplicate-suffix file family:
    - `summary 3.json`
    - `state 3.json`
    - `state.json 3.sha256`
    - `sequence_state 3.json`
    - `events 3.jsonl`
    - `soak_report 3.md`
  - retained empty residue directories:
    - `a1_inbox/`
    - `a1_strategies 2/`
    - `outbox 2/`
    - `reports 2/`
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
  - this pass processes only `TEST_STATE_TRANSITION_CHAIN_A` and does not reopen sibling `TEST_STATE_TRANSITION_CHAIN_B`
  - the archive value is a mixed run object with two executed state transitions, one queued third strategy, explicit sequence counters, and exact duplicate top-level copies
  - this object is useful for demotion lineage because it preserves step-count drift, replay-attribution versus `needs_real_llm true`, schema-fail second-step residue, queued continuation over final state hash, mixed survivor lineage, and packaging duplication
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_B`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A`
- source class: mixed executed-run plus queued-continuation root
- retained top-level contents:
  - `a1_inbox/`
  - `a1_strategies 2/`
  - `events 3.jsonl`
  - `events.jsonl`
  - `outbox 2/`
  - `reports 2/`
  - `sequence_state 3.json`
  - `sequence_state.json`
  - `soak_report 3.md`
  - `soak_report.md`
  - `state 3.json`
  - `state.json`
  - `state.json 3.sha256`
  - `state.json.sha256`
  - `summary 3.json`
  - `summary.json`
  - `zip_packets/`

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/summary.json`
- source class: primary terminal run summary
- summary markers:
  - `run_id TEST_STATE_TRANSITION_CHAIN_A`
  - `a1_source replay`
  - `needs_real_llm true`
  - `steps_completed 3`
  - `steps_requested 3`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `sim_registry_count 3`
  - `unresolved_promotion_blocker_count 3`
  - `stop_reason A2_OPERATOR_SET_EXHAUSTED`
  - retained digest diversity:
    - `unique_strategy_digest_count 3`
    - `unique_export_content_digest_count 3`
    - `unique_export_structural_digest_count 3`
  - `final_state_hash 3ce0407fab9f620d58362b73726db57ff29d25efdd200b7e48d8d68e9852fd65`
  - promotion counts by tier:
    - `T0_ATOM fail 1 pass 0`
    - `T1_COMPOUND fail 2 pass 0`
    - `T2_OPERATOR` through `T6_WHOLE_SYSTEM` all `0/0`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/state.json`
- source class: primary retained final state
- compact state markers:
  - `accepted_batch_count 2`
  - `canonical_ledger_len 2`
  - canonical previous-state hashes:
    - step `1`: `7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`
    - step `2`: `63995c34d867895591e52acf86da07ea9bd6d96de0c1a0de2d9afb7039fb1000`
  - `evidence_tokens_len 2`
  - evidence tokens:
    - `E_BIND_ALPHA`
    - `E_BIND_ALPHA_ALT`
  - `probe_meta_len 2`
  - `reject_log_len 1`
  - reject detail:
    - `SCHEMA_FAIL / ITEM_PARSE / STAGE_2_SCHEMA_CHECK`
  - `sim_promotion_status_len 3`
  - sim promotion states:
    - all retained entries are `PARKED`
  - `sim_registry_len 3`
  - retained sim ids:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - `S_BIND_ALPHA_S0001`
  - `sim_results_len 2`
  - `survivor_ledger_len 7`
  - retained survivor ids:
    - `F01_FINITUDE`
    - `N01_NONCOMMUTATION`
    - `P_BIND_ALPHA`
    - `P_BIND_ALPHA_ALT`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - `S_BIND_ALPHA_S0001`
  - `evidence_pending_len 0`
  - `kill_log_len 0`
- archive meaning:
  - final state preserves only two accepted batches and a mixed survivor set: the alternative lane advances to `S0002`, while the target lane remains at `S0001`

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/state.json.sha256`
- source class: primary state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/sequence_state.json`
- source class: retained sequence counters
- counter markers:
  - `A0 2`
  - `A1 3`
  - `A2 0`
  - `B 2`
  - `SIM 2`
- archive meaning:
  - sequence counters preserve a queued third A1 step without matching third-step execution packets from A0, B, or SIM

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/events.jsonl`
- source class: primary executed event ledger
- event markers:
  - retained line count: `2`
  - retained rows omit explicit `event` field and act as step-result rows
  - retained execution steps:
    - `1`
    - `2`
  - totals across retained rows:
    - `accepted 7`
    - `parked 0`
    - `rejected 1`
  - step `1` markers:
    - `accepted 4`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 2`
    - `state_hash_before 7c6fbf60826eaf185e71e9329873beddeda9baa2f9ce956626b97115e8bafc89`
    - `state_hash_after fcb5d2fe5a693a675ab749e15acc5baeeadc412c596aa076ee32c46c718fa1ba`
    - `sim_outputs 2`
  - step `2` markers:
    - `accepted 3`
    - `rejected 1`
    - `reject_tags SCHEMA_FAIL`
    - `repeated_schema_fail 1`
    - `unresolved_promotion_blocker_count 3`
    - `state_hash_before 63995c34d867895591e52acf86da07ea9bd6d96de0c1a0de2d9afb7039fb1000`
    - `state_hash_after 232c159561e591ff2213b51d332c2e766bee83bac5211b3216a4eb76040f6b54`
- archive meaning:
  - the executed ledger preserves only two completed state transitions even though summary and sequence counters preserve a third A1 step

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/soak_report.md`
- source class: primary human-readable stop report
- report markers:
  - `cycle_count 3`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `stop_reason A2_OPERATOR_SET_EXHAUSTED`
  - top failure tags:
    - `SCHEMA_FAIL 1`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/{summary 3.json,state 3.json,state.json 3.sha256,sequence_state 3.json,events 3.jsonl,soak_report 3.md}`
- source class: exact duplicate packaging-residue family
- duplication result:
  - each suffixed ` 3` file is byte-identical to its unsuffixed primary counterpart
  - no additional state, event, sequence, or soak information is introduced
- archive meaning:
  - treat the suffixed family as packaging duplication, not as a separate runtime branch

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/{a1_inbox,a1_strategies 2,outbox 2,reports 2}`
- source class: empty residue directories
- retained contents:
  - none
- archive meaning:
  - these directory shells are present but empty and add no executed runtime evidence

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/`
- source class: two-step executed lattice plus queued third strategy
- packet file count: `9`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 2`
  - `A1_TO_A0_STRATEGY_ZIP 3`
  - `B_TO_A0_STATE_UPDATE_ZIP 2`
  - `SIM_TO_A0_SIM_RESULT_ZIP 2`
- archive meaning:
  - the lattice preserves two executed full loops and one queued third A1 strategy without matching third-step downstream packets

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: first strategy packet
- sha256: `1bf1340891862afd2dfef6feca2f43c4db6781cb803a0da5bae448a49a501054`
- size bytes: `1907`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: second strategy packet
- sha256: `fc065383ea615155ba2a091c2aadc95e0a77460e213a75c76865a4ff22a94cf1`
- size bytes: `1901`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - target:
    - `S_BIND_ALPHA_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - negative class empty
  - alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - negative class `NEG_BOUNDARY`
  - `inputs.state_hash 63995c34d867895591e52acf86da07ea9bd6d96de0c1a0de2d9afb7039fb1000`

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: queued third strategy packet
- sha256: `302c40f0a028dd07e25c4804849fb1c6778bef79d3beae564752ca470a85a705`
- size bytes: `1906`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - target:
    - `S_BIND_ALPHA_S0003`
    - family `BOUNDARY_SWEEP`
    - tier `T1_COMPOUND`
    - negative class empty
  - alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0003`
    - family `BOUNDARY_SWEEP`
    - tier `T1_COMPOUND`
    - negative class `NEG_BOUNDARY`
  - `inputs.state_hash 3ce0407fab9f620d58362b73726db57ff29d25efdd200b7e48d8d68e9852fd65`
- archive meaning:
  - the third strategy packet is rooted on the retained final state hash, but no matching third-step `A0_TO_B`, `B_TO_A0`, or `SIM_TO_A0` packet survives

### Source 14
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- source class: second export packet
- sha256: `313ba61a0bcf02bad7813404ffb64ed761068d509058a3ac9157d7979795e543`
- size bytes: `1421`
- payload markers:
  - target spec:
    - `S_BIND_ALPHA_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - negative class empty
  - alternative spec:
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - negative class `NEG_BOUNDARY`

### Source 15
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
- source class: second Thread-S snapshot packet
- sha256: `988e7211a78343121234df88a58a3176b95b9c490c010e6dbd579cb6ed396381`
- size bytes: `1609`
- payload markers:
  - retained survivor ids:
    - `F01_FINITUDE`
    - `N01_NONCOMMUTATION`
    - `P_BIND_ALPHA`
    - `P_BIND_ALPHA_ALT`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - `S_BIND_ALPHA_S0001`
  - `EVIDENCE_PENDING EMPTY`
  - provenance:
    - `ACCEPTED_BATCH_COUNT=2`

### Source 16
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/TEST_STATE_TRANSITION_CHAIN_A/zip_packets/{000001_SIM_TO_A0_SIM_RESULT_ZIP.zip,000002_SIM_TO_A0_SIM_RESULT_ZIP.zip}`
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
