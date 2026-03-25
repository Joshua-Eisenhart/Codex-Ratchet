# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0002__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_QIT_AUTORATCHET_PASS`
Batch scope: archive-only intake of `RUN_QIT_AUTORATCHET_0002`, bounded to the direct run root, core run-state surfaces, both retained sequence ledgers, the embedded packet lattice, and the consumed strategy lane
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002`
  - core run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
    - `zip_packets/`
  - inbox residue surfaces:
    - `a1_inbox/sequence_state.json`
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the direct run `RUN_QIT_AUTORATCHET_0002` and does not reopen sibling runs
  - the archive value is a queue-drained autoratchet run whose single-step headline compresses five retained `step_result` passes and a larger semantic reject burden
  - the run is especially useful for historical packet-lineage audit because every same-name consumed-versus-embedded strategy packet pair differs byte-for-byte
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0003`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002`
- source class: direct autoratchet run root
- total files: `35`
- total directories: `3`
- top-level entries:
  - `a1_inbox`
  - `events.jsonl`
  - `sequence_state.json`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets`
- notable absences:
  - no wrapper README
  - no `HARDMODE_METRICS.json`
  - no `sim/` directory

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/summary.json`
- sha256: `30929abc2ca7bc3869caf4f2714fc952485a260ae8948bbbff02c5ade9696aba`
- size bytes: `834`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_QIT_AUTORATCHET_0002`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 4`
  - `parked_total 1`
  - `rejected_total 10`
  - `sim_registry_count 13`
  - `unresolved_promotion_blocker_count 13`
  - `stop_reason MAX_STEPS`
  - `final_state_hash 68876d8015418d064912ae1473833873ee6db50bc1bcb64d6bea7b076ea52887`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 8 pass 0`
    - `T1_COMPOUND fail 5 pass 0`
    - higher tiers all zero

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/state.json`
- sha256: `68876d8015418d064912ae1473833873ee6db50bc1bcb64d6bea7b076ea52887`
- size bytes: `52339`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 5`
  - `canonical_ledger_len 5`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 2`
  - `evidence_tokens_len 7`
  - `interaction_counts_len 5`
  - `kill_log_len 4`
  - `park_set_len 3`
  - `reject_log_len 33`
  - `sim_promotion_status_len 13`
  - `sim_registry_len 13`
  - `sim_results_len 7`
  - `survivor_ledger_len 28`
  - `survivor_order_len 28`
  - `term_registry_len 2`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - kill log retains four kill signals:
    - `S000001_SIM_KILL_NEG_FINITE_DIMENSIONAL_HILBERT_SPACE`
    - `S000001_MATH_NEG_FINITE_DIMENSIONAL_HILBERT_SPACE`
    - `S000002_SIM_KILL_NEG_DENSITY_MATRIX`
    - `S000002_MATH_NEG_DENSITY_MATRIX`
  - `park_set` retains three near-redundant semidefinite sims:
    - `S000003_SIM_CANON_SEMIDEFINITE`
    - `S000004_SIM_CANON_SEMIDEFINITE`
    - `S000005_SIM_CANON_SEMIDEFINITE`
  - `evidence_pending` retains two canonical evidence obligations:
    - `S000001_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE -> E_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE`
    - `S000002_CANON_DENSITY_MATRIX -> E_CANON_DENSITY_MATRIX`
  - all `13` `sim_promotion_status` entries are `PARKED`

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/sequence_state.json`
- sha256: `5b712d5622541494e7ed431da78bd8cdc0a4ad347d7e1bd954101c85e316d525`
- size bytes: `91`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 6`
  - `A1 5`
  - `A2 0`
  - `B 5`
  - `SIM 7`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/a1_inbox/sequence_state.json`
- sha256: `d8152e3dbab708a93f2b143c4e549c5c05b7c1b4f23f938725cffbdd48ec626d`
- size bytes: `34`
- source class: inbox-local A1 sequence ledger
- retained marker:
  - `RUN_QIT_AUTORATCHET_0002|A1 -> 5`
- relation to root sequence ledger:
  - root and inbox ledgers are not identical JSON shapes
  - both preserve the same terminal A1 sequence max of `5`

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/events.jsonl`
- sha256: `9eb900c409c4eca85d128ba021b181324d248971bcc38578a0ee4141ca6010c3`
- size bytes: `9211`
- line count: `6`
- source class: compact autoratchet event ledger
- event markers:
  - event kinds:
    - `a1_strategy_request_emitted`: `1`
    - `step_result`: `5`
  - step values present:
    - `1`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000004_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000005_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000006_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim result packet count: `7`
- retained compression marker:
  - five separate `step_result` rows all survive under the single logical step value `1`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/soak_report.md`
- sha256: `1b99e163d4caac6af37c50462088d3968986fd12c97f84b02452485e486e8bde`
- size bytes: `9420`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 4`
  - `parked_total 1`
  - `rejected_total 10`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `SCHEMA_FAIL 3`
    - `UNDEFINED_TERM_USE 3`
- retained event texture:
  - the embedded last-event window preserves five result rows over strategy packets `000001` through `000005`
  - the first two retained rows show `accepted 7`
  - later retained rows show `accepted 4`, `parked 1`, `rejected 10`

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/zip_packets`
- source class: embedded packet lattice
- file count: `23`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `5`
  - `A1_TO_A0_STRATEGY_ZIP`: `5`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `5`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `7`
- embedded strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> c9ddfe662f5267063c6adf6f5910eb7ef3252c5313e0ab73643e6dc57e042f8f`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 20259de736106cbd6ce677430ef418da1e8f56acf1aa18e2298f7be7a6130337`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 39793027e0630164a06376c488dccf421281655663816e67fb03e3ee54cf7b82`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> 436c54c70c6fe6ccd586527485a621cba55016f7c4695f59ff16e63f57a47df3`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 530e43e4533a545f63c01868b8d8d76baef7f7208a0c47d8b5bd1de6d381d366`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0002/a1_inbox/consumed`
- source class: fully consumed strategy residue
- file count: `5`
- consumed strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> 579fd67b87ac0b84c9fef6226eab47f783da05908061ad29c9fe4a40d12f852a`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> d9ade6250fdbc35321bd31841548cdee03e5c8e9d430b77e634c1a20caf4bd28`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> ef6e7dec39f185c87755250bbd3a1b5d1b5935c800af462505573e8421534534`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> d42e69ebd7222f3a0d6f774bf71866e5c6fac188fa63a8de78590f24b1aaa1e8`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> b2a23231c589b7f6191a27af9771d9ce6cf01f5e7b65a6e13ea8032125c1cb9f`
- lane relation to embedded strategy packets:
  - same five filenames appear in both consumed and embedded lanes
  - all five same-name pairs differ byte-for-byte
  - no live unconsumed strategy packets remain in `a1_inbox/`

## 3) Structural Map Of The Sources
### Segment A: queue-drained autoratchet direct run root
- source anchors:
  - run root inventory
  - `a1_inbox/consumed/`
  - `a1_inbox/sequence_state.json`
- source role:
  - preserves a direct autoratchet run captured after strategy-lane drain rather than during live queue backlog
- strong markers:
  - no wrapper README
  - five consumed strategy packets survive
  - no live strategy packet files remain in `a1_inbox/`

### Segment B: one-step headline over five retained passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves step compression where multiple retained result passes are collapsed into a single completed step
- strong markers:
  - `steps_completed 1`
  - `events.jsonl` keeps five `step_result` rows
  - all retained result rows use step value `1`

### Segment C: dual sequence ledgers with partial alignment
- source anchors:
  - root `sequence_state.json`
  - `a1_inbox/sequence_state.json`
- source role:
  - preserves both global and inbox-local views of terminal sequence state
- strong markers:
  - root ledger keeps source maxima for `A0`, `A1`, `A2`, `B`, and `SIM`
  - inbox ledger keeps only `RUN_QIT_AUTORATCHET_0002|A1 -> 5`
  - A1 maxima align at `5` even though the JSON shapes differ

### Segment D: semantic demotion pileup under a narrow headline
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves the larger semantic burden that survives underneath a narrow single-cycle summary window
- strong markers:
  - `kill_log_len 4`
  - `park_set_len 3`
  - `reject_log_len 33`
  - `evidence_pending_len 2`
  - all `13` sim promotion statuses are `PARKED`

### Segment E: same-name strategy-family instability across lanes
- source anchors:
  - `zip_packets/`
  - `a1_inbox/consumed/`
- source role:
  - preserves a full five-packet family where filename identity is not enough to recover byte identity
- strong markers:
  - same names `000001` through `000005` exist in both lanes
  - all five consumed-versus-embedded pairs diverge byte-for-byte

