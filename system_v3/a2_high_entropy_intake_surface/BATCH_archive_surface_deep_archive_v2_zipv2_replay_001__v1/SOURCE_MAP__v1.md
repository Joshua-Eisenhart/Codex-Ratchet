# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
Extraction mode: `ARCHIVE_DEEP_V2_ZIPV2_REPLAY_001_PASS`
Batch scope: archive-only intake of `V2_ZIPV2_REPLAY_001`, bounded to its retained run-core files, empty inbox residue, and nine-packet replay lattice including a queued third strategy packet
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001`
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
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
- reason for bounded family batch:
  - this pass processes only `V2_ZIPV2_REPLAY_001` and does not reopen other archive families
  - the archive value is a replay-authored object with a two-step executed spine, a queued third strategy rooted on final state, and several hidden closure seams between event endpoints, summary/state hash, and retained packet lineage
  - this object is useful for demotion lineage because it preserves replay-mode orchestration, schema-fail residue, empty inbox after queued continuation generation, and packet-facing evidence richer than final bookkeeping
- deferred next bounded batch in folder order:
  - none within `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001`
- source class: replay-authored ZIPv2 run root
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/summary.json`
- source class: terminal run summary
- summary markers:
  - `run_id V2_ZIPV2_REPLAY_001`
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
  - `final_state_hash b26e5e1d68ca8b50f637aa078a0484d9875c496db658b802efa1d28f7bbe780b`
  - promotion counts by tier:
    - `T0_ATOM fail 1 pass 0`
    - `T1_COMPOUND fail 2 pass 0`
    - all higher tiers `0/0`

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/state.json`
- source class: retained final state
- compact state markers:
  - `accepted_batch_count 2`
  - `evidence_tokens_len 2`
  - evidence tokens:
    - `E_BIND_ALPHA`
    - `E_BIND_ALPHA_ALT`
  - `probe_meta_len 2`
  - retained probe ids:
    - `P_BIND_ALPHA`
    - `P_BIND_ALPHA_ALT`
  - `reject_log_len 1`
  - reject tags:
    - `SCHEMA_FAIL`
  - `sim_promotion_status_len 3`
  - sim promotion states:
    - all retained entries are `PARKED`
  - `sim_registry_len 3`
  - retained sim ids:
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - `S_BIND_ALPHA_S0001`
  - `sim_results_len 2`
  - `survivor_ledger_len 5`
  - retained survivor ids:
    - `P_BIND_ALPHA`
    - `S_BIND_ALPHA_S0001`
    - `P_BIND_ALPHA_ALT`
    - `S_BIND_ALPHA_ALT_ALT_S0001`
    - `S_BIND_ALPHA_ALT_ALT_S0002`
  - `evidence_pending_len 0`
  - `kill_log_len 0`
- archive meaning:
  - final state preserves two earned batches and a queued third-step boundary sweep only as proposal residue; the target `S_BIND_ALPHA_S0002` and all `S0003` survivors are absent from final state

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches `state.json`
  - declared hash matches `summary.json` final hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/events.jsonl`
- source class: executed event ledger
- event markers:
  - retained line count: `2`
  - retained row shape:
    - both rows are step-result variants without explicit `event`
  - retained steps:
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
    - `state_hash_before de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
    - `state_hash_after 8f4b8d3d39fb49166d6858d7d842717763056f61c6c228fcbac6930821f9721b`
    - `sim_outputs_len 2`
  - step `2` markers:
    - `accepted 3`
    - `rejected 1`
    - `reject_tags [SCHEMA_FAIL]`
    - `unresolved_promotion_blocker_count 3`
    - `state_hash_before ac87f69832bbff473afdcebe5fde17d5f08166680b7243f3aea9de0ac0518bee`
    - `state_hash_after 3f67cddcfab0adf02f58b521046895b67381c8a0dcdb4916e5700dc385590408`
- archive meaning:
  - the executed ledger preserves only two steps even though summary and soak count three cycles

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/soak_report.md`
- source class: human-readable stop report
- report markers:
  - `cycle_count 3`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 1`
  - `stop_reason A2_OPERATOR_SET_EXHAUSTED`
  - top failure tags:
    - `SCHEMA_FAIL: 1`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/a1_inbox/`
- source class: empty inbox residue
- retained contents:
  - none
- archive meaning:
  - no live or consumed A1 inbox packet survives even though a third strategy packet is retained under `zip_packets/`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/zip_packets/`
- source class: replay packet lattice
- packet file count: `9`
- packet kind counts:
  - `A0_TO_B_EXPORT_BATCH_ZIP 2`
  - `A1_TO_A0_STRATEGY_ZIP 3`
  - `B_TO_A0_STATE_UPDATE_ZIP 2`
  - `SIM_TO_A0_SIM_RESULT_ZIP 2`

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: first executed strategy packet
- sha256: `edcb2971ffd3f9a7f8702d3ff34f9ccc5aa36a9440812cbdb797d5efc5f455d8`
- size bytes: `1903`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - `inputs.state_hash de0e5fe905c27b70960a8a41dadfe10ac8ab9beef13ea3a6724d7d7630d353cc`
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

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: second executed strategy packet
- sha256: `4cf5f2b07164114d42dc335364c7b2dc908361812a67eedaa036f02ea02fb590`
- size bytes: `1897`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - `inputs.state_hash ac87f69832bbff473afdcebe5fde17d5f08166680b7243f3aea9de0ac0518bee`
  - target:
    - `S_BIND_ALPHA_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - empty `NEGATIVE_CLASS`
  - alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0002`
    - family `BASELINE`
    - tier `T0_ATOM`
    - `NEGATIVE_CLASS NEG_BOUNDARY`

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- source class: queued third strategy packet
- sha256: `40543adcfef35090a9255bc5621f3f8b51dfa55f99c3f5111e405130db02d1c6`
- size bytes: `1899`
- payload markers:
  - `strategy_id STRAT_SAMPLE_0001`
  - `inputs.state_hash b26e5e1d68ca8b50f637aa078a0484d9875c496db658b802efa1d28f7bbe780b`
  - target:
    - `S_BIND_ALPHA_S0003`
    - family `BOUNDARY_SWEEP`
    - tier `T1_COMPOUND`
    - empty `NEGATIVE_CLASS`
  - alternative:
    - `S_BIND_ALPHA_ALT_ALT_S0003`
    - family `BOUNDARY_SWEEP`
    - tier `T1_COMPOUND`
    - `NEGATIVE_CLASS NEG_BOUNDARY`
- archive meaning:
  - the third step survives only as a queued packet rooted on the final snapshot hash, not as an executed event or final survivor set

### Source 12
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/{zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip,zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip}`
- source class: executed export pair
- payload markers:
  - first export sha256/size:
    - `84a63335261c344445561cbbde24c2c92b2d0a6eb2ff67e9f6cd4bea1db7575a`
    - `1403`
  - second export sha256/size:
    - `6faa9e16670f085deaf2477e0c85227b60e2331a8af8c8489ee33e3ecf9ccaa0`
    - `1405`
  - first export keeps both `S0001` lanes at `T1_COMPOUND / PERTURBATION / NEG_BOUNDARY`
  - second export advances both lanes to `S0002` and `T0_ATOM / BASELINE`, while the target lane leaves `NEGATIVE_CLASS` blank

### Source 13
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/{zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip,zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip}`
- source class: Thread-S snapshot pair
- payload markers:
  - first snapshot sha256/size:
    - `21b9c4edaa2ac631160a776795cd6a6f7786a8ae49bdf3a4fcf3d7f2edd7652f`
    - `1492`
  - second snapshot sha256/size:
    - `bfcbd546c788e49e412527b585a8139ce78867072a6b0f9273d4162385a37aa8`
    - `1536`
  - first snapshot keeps `EVIDENCE_PENDING` for both `S0001` specs
  - second snapshot clears `EVIDENCE_PENDING`
  - second snapshot survivor ledger includes `S_BIND_ALPHA_ALT_ALT_S0002` but not `S_BIND_ALPHA_S0002`

### Source 14
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/V2_ZIPV2_REPLAY_001/{zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip,zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip}`
- source class: retained SIM evidence pair
- payload markers:
  - first sim packet sha256/size:
    - `431622bd121c8071cb159e0e9e4dd0f13cd1d371236dc2bc4d54a52990bf6628`
    - `1393`
  - second sim packet sha256/size:
    - `e585ddda09fdd52c488a7e813c9fa76c53d2a270d630f0de9ebbf4aacec1219d`
    - `1385`
  - both retained SIM packets emit `KILL_SIGNAL NEG_NEG_BOUNDARY`
  - retained evidence signals:
    - `E_BIND_ALPHA_ALT`
    - `E_BIND_ALPHA`
