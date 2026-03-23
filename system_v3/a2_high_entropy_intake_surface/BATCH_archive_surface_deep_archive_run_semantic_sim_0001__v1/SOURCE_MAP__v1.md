# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_semantic_sim_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_SEMANTIC_SIM_PASS`
Batch scope: archive-only intake of `RUN_SEMANTIC_SIM_0001`, bounded to the direct run root, core run-state surfaces, the root sequence ledger, the inbox consumed lane, and the embedded packet lattice
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001`
  - core run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
    - `zip_packets/`
  - inbox residue surfaces:
    - `a1_inbox/`
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the direct run `RUN_SEMANTIC_SIM_0001` and does not reopen sibling runs
  - the archive value is a semantic-SIM expansion run with five coherent accepted steps, thirty SIM outputs, and no packet parks or rejects
  - the run is especially useful for demotion lineage because clean transport and accurate summary counters still end with thirty `PARKED` sim promotion states, five pending canonical evidence items, no inbox-local sequence ledger, and a renumbered consumed strategy lane
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SIGNAL_0002`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001`
- source class: direct semantic-sim run root
- total files: `57`
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
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/summary.json`
- sha256: `f58c539a8c241699fa43046df5a1612ce4bcd6cabffcdcbd39ac37c9a0b4501e`
- size bytes: `832`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_SEMANTIC_SIM_0001`
  - `steps_completed 5`
  - `steps_requested 5`
  - `accepted_total 70`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 30`
  - `unresolved_promotion_blocker_count 30`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 5`
  - `unique_export_structural_digest_count 5`
  - `unique_strategy_digest_count 5`
  - `final_state_hash 711063559a9219f16fb8b0e81020004d9bad7f4979cc8f94cabcc6036d583c57`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 5 pass 0`
    - `T1_COMPOUND fail 15 pass 0`
    - `T2_OPERATOR fail 5 pass 0`
    - `T3_STRUCTURE fail 5 pass 0`
    - higher tiers all zero

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/state.json`
- sha256: `711063559a9219f16fb8b0e81020004d9bad7f4979cc8f94cabcc6036d583c57`
- size bytes: `87702`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 5`
  - `canonical_ledger_len 5`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 5`
  - `evidence_tokens_len 30`
  - `interaction_counts_len 20`
  - `kill_log_len 10`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 30`
  - `sim_registry_len 30`
  - `sim_results_len 30`
  - `survivor_ledger_len 72`
  - `survivor_order_len 72`
  - `term_registry_len 15`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains five canonical evidence keys:
    - `S_CANON_A_0001`
    - `S_CANON_A_0002`
    - `S_CANON_A_0003`
    - `S_CANON_A_0004`
    - `S_CANON_A_0005`
  - `kill_log` retains ten kill signals split evenly across:
    - `NEG_COMMUTATIVE_ASSUMPTION`
    - `NEG_CLASSICAL_TIME`
  - `park_set` is empty
  - `reject_log` is empty
  - all `30` `sim_promotion_status` entries are `PARKED`
  - retained sim ids split into five repeated families:
    - `BASE`
    - `BOUND`
    - `NEG_A`
    - `NEG_B`
    - `PERT`
    - `STRESS`

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/sequence_state.json`
- sha256: `ded38c41bf4b9ca221bed2baf863263d900226b6393335d4741174cec80e3231`
- size bytes: `89`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 6`
  - `A1 5`
  - `A2 0`
  - `B 5`
  - `SIM 30`

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/a1_inbox`
- source class: inbox residue without local sequence ledger
- top-level entries:
  - `consumed/`
- retained meaning:
  - no `a1_inbox/sequence_state.json` exists for this run
  - the inbox retains only the consumed packet lane

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/events.jsonl`
- sha256: `feaa0b44b463e67fc8d3427746b0b8210d6f6ca9b3de77fed878b76badc14631`
- size bytes: `18011`
- line count: `6`
- source class: semantic-sim event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `5`
  - step values present:
    - `1`
    - `2`
    - `3`
    - `4`
    - `5`
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
  - referenced sim outputs total: `30`
  - retained digest diversity:
    - `5` distinct strategy digests
    - `5` distinct export content digests
    - `5` distinct export structural digests
- retained pass progression:
  - steps `1` through `5` each preserve:
    - `accepted 14`
    - `parked 0`
    - `rejected 0`
    - `6` sim outputs
  - unresolved blocker counts rise linearly:
    - `6`
    - `12`
    - `18`
    - `24`
    - `30`

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/soak_report.md`
- sha256: `e75df4fd9fa3b8b927c6fd7f96a1dc733d7e234671d03f20c3913f212476e92f`
- size bytes: `18186`
- source class: human-readable soak report
- report markers:
  - `cycle_count 5`
  - `accepted_total 70`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `NONE`
- retained event texture:
  - the last-event window preserves five accepted result rows over strategy packets `000001` through `000005`
  - each retained row shows `accepted 14`, `parked 0`, `rejected 0`
  - runtime-like `sim/sim_evidence_*` paths are preserved in all SIM outputs even though no local `sim/` directory exists

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/zip_packets`
- source class: embedded packet lattice
- file count: `46`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `5`
  - `A1_TO_A0_STRATEGY_ZIP`: `5`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `5`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `30`
- embedded strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> 1eda36d29c64c9e3f98652e40a410227e96b09b1a7d8d8da6f5a68239f33ec48`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 43c5fb7fc467f224179941dbbe259d7ead9fb7e34628cd8f04e749cb59ab723e`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 2f56c1109c65ac390d6f7dc73b0c2167c3517a7b5347636458fe7aa570cefd30`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> 952f4ca1a78870829a0628e174eb1e347108f84a3439cad64fd9a649e88c894b`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 91e2b38cdce9ae3284b1fc97df7dbb14744aeafda5f62b10b2d879cc0f2c58d0`

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_SEMANTIC_SIM_0001/a1_inbox/consumed`
- source class: renumbered consumed strategy residue
- file count: `5`
- consumed strategy packet hashes:
  - `400001_A1_TO_A0_STRATEGY_ZIP.zip -> 1eda36d29c64c9e3f98652e40a410227e96b09b1a7d8d8da6f5a68239f33ec48`
  - `400002_A1_TO_A0_STRATEGY_ZIP.zip -> 1c02cb76107dd52d1387fa82d5ce07333d3974077f8aa4cac5d0dd9945e853bf`
  - `400003_A1_TO_A0_STRATEGY_ZIP.zip -> 4cc639d0fd0b6399a51ddd40b05121f0be41cc285e798ffe281f1c4d9e8f5403`
  - `400004_A1_TO_A0_STRATEGY_ZIP.zip -> 35acb4ecff554f3ac304f292fb93e480079fc5df75e61a085e923708ffd32b9f`
  - `400005_A1_TO_A0_STRATEGY_ZIP.zip -> 947b9f89bf15893f2acbff6fa1f1283d408be0a1d6dcb83746f844cc82f276fa`
- lane relation to embedded strategy packets:
  - consumed and embedded strategy families do not share filenames
  - exactly one consumed packet is byte-identical to one embedded packet:
    - consumed `400001_A1_TO_A0_STRATEGY_ZIP.zip`
    - embedded `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - the other four consumed packets have no embedded byte-identical match
  - no live unconsumed strategy packets remain in `a1_inbox/`

## 3) Structural Map Of The Sources
### Segment A: five-step semantic-sim expansion run
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `zip_packets/`
- source role:
  - preserves a coherent five-step run with stable per-step output volume and growing unresolved semantic load
- strong markers:
  - `steps_completed 5`
  - each retained step accepts `14`
  - each retained step emits `6` SIM results
  - total SIM result packet count reaches `30`

### Segment B: clean packet counters over maximal parked sim debt
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves a large semantic burden even though packet transport remains clean
- strong markers:
  - summary and soak both report `parked_total 0` and `rejected_total 0`
  - `state.json` keeps `evidence_pending_len 5`, `kill_log_len 10`, and `30` parked sim promotion states
  - `promotion_counts_by_tier` records only failures and zero passes

### Segment C: no inbox-local sequence ledger
- source anchors:
  - `sequence_state.json`
  - `a1_inbox/`
- source role:
  - preserves a run family where only the root sequence ledger survives
- strong markers:
  - root `sequence_state.json` is present
  - `a1_inbox` contains only `consumed/`
  - `a1_inbox/sequence_state.json` is absent

### Segment D: renumbered consumed strategy lane
- source anchors:
  - `events.jsonl`
  - `zip_packets/`
  - `a1_inbox/consumed/`
- source role:
  - preserves a naming discontinuity between embedded strategy transport and consumed strategy residue
- strong markers:
  - embedded strategy files use `000001` through `000005`
  - consumed strategy files use `400001` through `400005`
  - only the first consumed packet is byte-identical to an embedded packet
  - the other four consumed packets do not byte-match any embedded strategy packet

### Segment E: summary fidelity on counts but not promotion truth
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `state.json`
- source role:
  - preserves an unusual case where headline step and digest counts match retained rows, yet promotion truth still fails closed
- strong markers:
  - summary digest counts are `5` and retained event digests are also `5`
  - summary accepted total `70` matches five steps of `accepted 14`
  - all `30` sim promotion states remain `PARKED`

