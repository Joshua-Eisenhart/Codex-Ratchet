# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
Extraction mode: `ARCHIVE_DEEP_V2_ZIPV2_PACKET_E2E_001_PASS`
Batch scope: archive-only intake of `V2_ZIPV2_PACKET_E2E_001`, bounded to its retained run-core files, consumed strategy copy, and five-packet ZIPv2 lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001`
  - retained run-core files:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `soak_report.md`
  - retained inbox residue:
    - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - retained packet family under `zip_packets/`:
    - `000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `000002_A0_TO_A1_SAVE_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `V2_ZIPV2_PACKET_E2E_001` and does not reopen sibling `V2_ZIPV2_PACKET_REQ_001`
  - the archive value is a compact ZIPv2 packet-loop object preserving one executed cycle, one external A1 save-request handoff, and a same-name strategy split between retained and consumed lanes
  - this object is useful for demotion lineage because transport looks clean while semantic closure remains open, final state sits above the only executed step-result row, and runtime-local path leakage survives after archival relocation
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_REQ_001`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001`
- source class: compact ZIPv2 packet-loop run root
- retained top-level contents:
  - `a1_inbox/`
  - `events.jsonl`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets/`
- missing top-level runtime surface:
  - `sequence_state.json`

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id V2_ZIPV2_PACKET_E2E_001`
  - `a1_source packet`
  - `needs_real_llm false`
  - `steps_completed 2`
  - `steps_requested 2`
  - `accepted_total 2`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 1`
  - `unresolved_promotion_blocker_count 1`
  - `stop_reason A1_NEEDS_EXTERNAL_STRATEGY`
  - retained digest diversity:
    - `unique_strategy_digest_count 1`
    - `unique_export_content_digest_count 1`
    - `unique_export_structural_digest_count 1`
  - `final_state_hash 5b0f04fea8ab507c859fb36e0cb16f56426aa30ad00c42cc2f4746122913bb8f`
  - promotion counts by tier:
    - `T1_COMPOUND fail 1 pass 0`
    - all other tiers `0/0`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/state.json`
- source class: retained final state
- compact state markers:
  - `accepted_batch_count 1`
  - `canonical_ledger_len 0`
  - `evidence_tokens_len 1`
  - evidence tokens:
    - `E_BIND_ALPHA`
  - `probe_meta_len 1`
  - retained probe id:
    - `P_BIND_ALPHA`
  - `reject_log_len 0`
  - `sim_promotion_status_len 1`
  - sim promotion states:
    - `PARKED`
  - `sim_registry_len 1`
  - retained sim ids:
    - `S_BIND_ALPHA_S0001`
  - `sim_results_len 1`
  - `survivor_ledger_len 2`
  - retained survivor ids:
    - `P_BIND_ALPHA`
    - `S_BIND_ALPHA_S0001`
  - `evidence_pending_len 0`
  - `kill_log_len 0`
- archive meaning:
  - final state preserves one accepted cycle and one retained SIM result, but canonical ledger, pending-evidence, and kill bookkeeping are thinner than the packet-facing residue

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/events.jsonl`
- source class: mixed executed/request event ledger
- event markers:
  - retained line count: `2`
  - retained row shapes:
    - step `1` is a step-result variant without explicit `event`
    - step `2` is explicit `a1_strategy_request_emitted`
  - retained steps:
    - `1`
    - `2`
  - totals across retained rows:
    - `accepted 2`
    - `parked 0`
    - `rejected 0`
  - step `1` markers:
    - `accepted 2`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 1`
    - `state_hash_before de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
    - `state_hash_after 3aede158a802eb4069e43580ff85ea5a307e192f39e269b7bf932d3f4a39f4a8`
    - `strategy_digest bc06a021f2d7c6bea798892b5560da0653a42c3883bcb31630f6f371028fb320`
    - `sim_outputs_len 1`
  - step `2` markers:
    - `event a1_strategy_request_emitted`
    - `state_hash 5b0f04fea8ab507c859fb36e0cb16f56426aa30ad00c42cc2f4746122913bb8f`
    - `source ZIP_PROTOCOL_v2`
    - `last_reject_tags []`
- archive meaning:
  - the run preserves one executed packet loop and then transitions into an outbound save-request state without keeping a second executed step-result row

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 2`
  - `accepted_total 2`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason A1_NEEDS_EXTERNAL_STRATEGY`
  - top failure tags:
    - `NONE`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/a1_inbox`
- source class: inbox residue
- retained contents:
  - `consumed/`
- archive meaning:
  - no live inbox strategy remains; only a consumed copy of the first step packet survives

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: consumed first-step strategy copy
- sha256: `2f205f5406753a0cef2799257bb8bbdceb07a5ae737171a78f322fd51f237fe4`
- payload markers:
  - `strategy_id STRAT_PACKET_E2E`
  - no alternatives retained
  - target:
    - `S_BIND_ALPHA`
    - `REQUIRES_EVIDENCE E_BIND_ALPHA`
  - `inputs.state_hash` is all zeroes
  - self audit is empty:
    - `alternative_count 0`
    - `candidate_count 0`
    - `compile_lane_digest ""`
    - `strategy_hash ""`

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/zip_packets`
- source class: retained ZIPv2 packet lattice
- packet file count: `5`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 1`
  - `A1_TO_A0_STRATEGY_ZIP 1`
  - `B_TO_A0_STATE_UPDATE_ZIP 1`
  - `SIM_TO_A0_SIM_RESULT_ZIP 1`
  - `A0_TO_A1_SAVE_ZIP 1`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: retained first-step strategy packet
- sha256: `18b3943e8071234fda2c8cce0c4085061694a75780d18611c2064fa4b9329492`
- size bytes: `1944`
- payload markers:
  - `strategy_id STRAT_PACKET_E2E`
  - target:
    - `S_BIND_ALPHA_S0001`
    - family `PERTURBATION`
    - tier `T1_COMPOUND`
    - `NEGATIVE_CLASS NEG_BOUNDARY`
  - alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - family `PERTURBATION`
    - tier `T1_COMPOUND`
    - `NEGATIVE_CLASS NEG_BOUNDARY`
  - `inputs.state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
  - self audit is populated:
    - `alternative_count 1`
    - `candidate_count 1`
    - `compile_lane_digest 237524147d099637e7d37fd265955b280afb14821bdccb721cb882d7fa392940`
    - `strategy_hash e46202f3b40eafe02c92a587d534a7d931049cfdc6aa1ebf500385ea2475e16d`

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/{zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip,a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip}`
- source class: same-name strategy divergence pair
- divergence markers:
  - relative packet name matches in both locations
  - packet bytes do not match
  - retained packet carries target plus alternative lanes and full tier/family/negative-class typing
  - consumed copy collapses to one generic target, no alternatives, and all-zero input-state hash
- archive meaning:
  - treat the pair as a historical contradiction surface, not as interchangeable copies of the same strategy packet

### Source 12
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- source class: executed export packet
- sha256: `b82faaa20d374ce1624598249561b61b506494fe0a2e0ac6d2113a074080a105`
- size bytes: `1326`
- payload markers:
  - target thread:
    - `THREAD_B_ENFORCEMENT_KERNEL`
  - retained export targets:
    - `P_BIND_ALPHA`
    - `S_BIND_ALPHA_S0001`
  - `REQUIRES_EVIDENCE E_BIND_ALPHA`
  - `SIM_ID S_BIND_ALPHA_S0001`
  - `TIER T1_COMPOUND`
  - `FAMILY PERTURBATION`
  - `TARGET_CLASS S_BIND_ALPHA_S0001_STEP_0001_C01`
  - `NEGATIVE_CLASS NEG_BOUNDARY`

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
- source class: Thread-S snapshot packet
- sha256: `646502e6de17ab0f5b4635751fad81df0654d267c577cb92d00ebbaf09adbf58`
- size bytes: `1425`
- payload markers:
  - `ACCEPTED_BATCH_COUNT=1`
  - retained survivor ids:
    - `P_BIND_ALPHA`
    - `S_BIND_ALPHA_S0001`
  - `EVIDENCE_PENDING` still lists:
    - `S_BIND_ALPHA_S0001 REQUIRES_EVIDENCE E_BIND_ALPHA`

### Source 14
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- source class: only retained SIM result packet
- sha256: `113170c422a2a815d8edf147026bf6e7ef114c9168387ef5dc10810ded588b53`
- size bytes: `1390`
- payload markers:
  - `SIM_ID S_BIND_ALPHA_S0001`
  - `TIER T1_COMPOUND`
  - `FAMILY PERTURBATION`
  - `TARGET_CLASS S_BIND_ALPHA_S0001_STEP_0001_C01`
  - `NEGATIVE_CLASS NEG_BOUNDARY`
  - `EVIDENCE_SIGNAL E_BIND_ALPHA`
  - `KILL_SIGNAL NEG_NEG_BOUNDARY`

### Source 15
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_PACKET_E2E_001/zip_packets/000002_A0_TO_A1_SAVE_ZIP.zip`
- source class: outbound save-request packet
- sha256: `6b3b82ff4136f3682b5610b541b8511a46a382cfa0e7cbb1ac7a0a2b91d8ea43`
- size bytes: `1882`
- payload markers:
  - `schema A0_SAVE_SUMMARY_v1`
  - `run_id V2_ZIPV2_PACKET_E2E_001`
  - `step 2`
  - `state_hash 5b0f04fea8ab507c859fb36e0cb16f56426aa30ad00c42cc2f4746122913bb8f`
  - `last_reject_tags []`
  - embedded base strategy is generic:
    - `strategy_id STRAT_SAMPLE_0001`
    - target `S_BIND_ALPHA`
    - alternative `S_BIND_ALPHA_ALT`
    - `inputs.state_hash` is all zeroes
    - placeholder digest hashes remain inlined
