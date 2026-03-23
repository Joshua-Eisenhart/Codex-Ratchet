# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_registry_smoke_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_REGISTRY_SMOKE_PASS`
Batch scope: archive-only intake of `RUN_REGISTRY_SMOKE_0001`, bounded to the direct run root, core run-state surfaces, both retained sequence ledgers, the embedded packet lattice, and the consumed strategy lane
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001`
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
  - this pass processes only the direct run `RUN_REGISTRY_SMOKE_0001` and does not reopen sibling runs
  - the archive value is a compact registry-smoke run that preserves the smallest clean transport surface in this family while still showing headline compression and semantic demotion debt
  - the run is especially useful for archive lineage because it compresses two accepted passes into one headline total, preserves empty-path SIM evidence references, and already shows same-name strategy-packet divergence
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001`
- source class: direct smoke run root
- total files: `20`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/summary.json`
- sha256: `defe0b49875bab578b28941d4b3dd9fbe4b6d0d60b0193e6d2456c2252927e9a`
- size bytes: `830`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_REGISTRY_SMOKE_0001`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 4`
  - `unresolved_promotion_blocker_count 4`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 1`
  - `unique_export_structural_digest_count 1`
  - `unique_strategy_digest_count 1`
  - `final_state_hash a014509a1c76b4ff7b9030c958d32a49f2ba96909d4876e251741649f15d577e`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 2 pass 0`
    - `T1_COMPOUND fail 2 pass 0`
    - higher tiers all zero

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/state.json`
- sha256: `a014509a1c76b4ff7b9030c958d32a49f2ba96909d4876e251741649f15d577e`
- size bytes: `25151`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 2`
  - `canonical_ledger_len 2`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 2`
  - `evidence_tokens_len 4`
  - `interaction_counts_len 2`
  - `kill_log_len 4`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 4`
  - `sim_registry_len 4`
  - `sim_results_len 4`
  - `survivor_ledger_len 16`
  - `survivor_order_len 16`
  - `term_registry_len 2`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains two canonical evidence obligations:
    - `S000001_Z_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE`
    - `S000002_Z_CANON_DENSITY_MATRIX`
  - `kill_log` retains four kill signals with tokens:
    - `NEG_INFINITE_SET`
    - `NEG_COMMUTATIVE_ASSUMPTION`
  - `park_set` is empty
  - `reject_log` is empty
  - all `4` `sim_promotion_status` entries are `PARKED`

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/sequence_state.json`
- sha256: `a2cd63aab6f53d01a35b699258a3d285ac69ecb47628f3f6eb78c86c03996da2`
- size bytes: `90`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 3`
  - `A1 2`
  - `A2 0`
  - `B 2`
  - `SIM 4`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/a1_inbox/sequence_state.json`
- sha256: `28aba5ac018fd7004dfab4878163ca638a30e376bdda9194b21a8a983af869f8`
- size bytes: `33`
- source class: inbox-local A1 sequence ledger
- retained marker:
  - `RUN_REGISTRY_SMOKE_0001|A1 -> 2`
- relation to root sequence ledger:
  - root and inbox ledgers are not identical JSON shapes
  - both preserve the same terminal A1 sequence max of `2`

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/events.jsonl`
- sha256: `cb11ee28b8854c475c62d9b45c0fd2b055ff67cba1408d4d7733e98d0deda775`
- size bytes: `3862`
- line count: `3`
- source class: compact smoke event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `2`
  - step values present:
    - `1`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim outputs total: `4`
  - retained digest diversity:
    - `2` distinct strategy digests
    - `2` distinct export content digests
    - `2` distinct export structural digests
- retained pass progression:
  - pass 1:
    - `accepted 7`
    - `parked 0`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 2`
  - pass 2:
    - `accepted 7`
    - `parked 0`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 4`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/soak_report.md`
- sha256: `32d261974502a3c1f250873fc384a502dfbdc930a9fb3a2eec20dd32b47cde81`
- size bytes: `4269`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 7`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`
  - `sim_tier_legend` is present
- retained event texture:
  - the last-event window preserves two retained result rows over strategy packets `000001` and `000002`
  - both retained rows show `accepted 7`, `parked 0`, `rejected 0`
  - all retained `sim_outputs[].path` values are empty strings

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/zip_packets`
- source class: embedded packet lattice
- file count: `11`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `2`
  - `A1_TO_A0_STRATEGY_ZIP`: `2`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `2`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `4`
- embedded strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> f3cbd525bc9a19a683ca6a329d061b62d55dd9ea92b7be86db3f1f9d4d10ea94`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 28ee0dfdf1bb10dc43cd39121d3c4e917b694c8204acc496ae32098db5382729`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001/a1_inbox/consumed`
- source class: fully consumed strategy residue
- file count: `2`
- consumed strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> e07040e87398eb4c8264a0ed5ea27b9d01eefa2f46bfb709388c30cbc256e4b7`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 2a7114ac74cce79a6ef2765ac6e117b4caed997be87575d3cfc0cc68a304174d`
- lane relation to embedded strategy packets:
  - same two filenames appear in both consumed and embedded lanes
  - both same-name pairs differ byte-for-byte
  - no live unconsumed strategy packets remain in `a1_inbox/`

## 3) Structural Map Of The Sources
### Segment A: minimal queue-drained smoke run
- source anchors:
  - run root inventory
  - `a1_inbox/consumed/`
  - `zip_packets/`
- source role:
  - preserves a direct smoke run with the smallest queue-drained transport surface in this archive family
- strong markers:
  - two consumed strategy packets survive
  - no live strategy packet files remain in `a1_inbox/`
  - packet lattice totals only `11` zip members

### Segment B: one-step headline over two accepted passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves headline compression where two accepted result passes are collapsed into one headline step and one accepted-total window
- strong markers:
  - `steps_completed 1`
  - `events.jsonl` keeps two accepted result rows
  - both retained rows show `accepted 7`
  - summary still reports `accepted_total 7`

### Segment C: clean packet counters over semantic promotion debt
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves semantic burden even though packet-level park/reject counters are clean
- strong markers:
  - headline counters end at `parked_total 0` and `rejected_total 0`
  - `state.json` keeps `evidence_pending_len 2`, `kill_log_len 4`, and all `4` sim promotion states as `PARKED`
  - soak top failure tags are `NONE`

### Segment D: digest-collapse summary over two-digest history
- source anchors:
  - `summary.json`
  - `events.jsonl`
- source role:
  - preserves the same digest-collapse pattern seen in larger runs, but in the smallest possible two-pass form
- strong markers:
  - summary records all unique digest counts as `1`
  - retained result rows preserve `2` distinct strategy, export-content, and export-structural digests

### Segment E: empty-path sim evidence references
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves SIM-result references without any evidence-body file path, not just missing local `sim/` retention
- strong markers:
  - all retained `sim_outputs[].path` fields are empty strings
  - the run root has no `sim/` directory

### Segment F: same-name strategy-family instability across two pairs
- source anchors:
  - `zip_packets/`
  - `a1_inbox/consumed/`
- source role:
  - preserves a compact proof that filename identity is not enough to recover payload identity
- strong markers:
  - same names `000001` and `000002` exist in both lanes
  - both consumed-versus-embedded pairs diverge byte-for-byte

