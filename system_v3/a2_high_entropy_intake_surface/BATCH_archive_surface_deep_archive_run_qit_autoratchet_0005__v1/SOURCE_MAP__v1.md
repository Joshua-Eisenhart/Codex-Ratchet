# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0005__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_QIT_AUTORATCHET_PASS`
Batch scope: archive-only intake of `RUN_QIT_AUTORATCHET_0005`, bounded to the direct run root, core run-state surfaces, both retained sequence ledgers, the embedded packet lattice, and the consumed strategy lane
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005`
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
  - this pass processes only the direct run `RUN_QIT_AUTORATCHET_0005` and does not reopen sibling runs
  - the archive value is an eight-pass queue-drained autoratchet run whose summary remains flat while the retained state expands into `trace_one` and `CPTP_channel` families
  - the run is especially useful for demotion lineage because it combines digest-collapse summary reporting, eight same-name strategy-packet mismatches, and a semantic shift from `SCHEMA_FAIL`/`NEAR_REDUNDANT` pressure toward explicit `PROBE_PRESSURE`
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_REGISTRY_SMOKE_0001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005`
- source class: direct autoratchet run root
- total files: `52`
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
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/summary.json`
- sha256: `2c19d2fc4777065814c2448308c336751fad08f55892b58576738b015b22d78e`
- size bytes: `834`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_QIT_AUTORATCHET_0005`
  - `steps_completed 1`
  - `steps_requested 1`
  - `accepted_total 3`
  - `parked_total 2`
  - `rejected_total 2`
  - `sim_registry_count 18`
  - `unresolved_promotion_blocker_count 18`
  - `stop_reason MAX_STEPS`
  - `unique_export_content_digest_count 1`
  - `unique_export_structural_digest_count 1`
  - `unique_strategy_digest_count 1`
  - `final_state_hash 5eb5a88e4544dfde14ecb02054a0ec6ed249c932fe4c4133dc63e5f6954c528a`
  - `promotion_counts_by_tier`:
    - `T0_ATOM fail 10 pass 0`
    - `T1_COMPOUND fail 8 pass 0`
    - higher tiers all zero

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/state.json`
- sha256: `5eb5a88e4544dfde14ecb02054a0ec6ed249c932fe4c4133dc63e5f6954c528a`
- size bytes: `89530`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 8`
  - `canonical_ledger_len 8`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 8`
  - `evidence_tokens_len 12`
  - `interaction_counts_len 6`
  - `kill_log_len 8`
  - `park_set_len 10`
  - `reject_log_len 16`
  - `sim_promotion_status_len 18`
  - `sim_registry_len 18`
  - `sim_results_len 12`
  - `survivor_ledger_len 54`
  - `survivor_order_len 54`
  - `term_registry_len 8`
  - `active_megaboot_id` empty
  - `active_megaboot_sha256` empty
  - `active_ruleset_sha256` empty
- retained state markers:
  - `evidence_pending` retains eight canonical evidence obligations:
    - finite-dimensional Hilbert space
    - density matrix
    - positive
    - semidefinite
    - positive semidefinite
    - one
    - trace one
    - CPTP channel
  - `kill_log` retains eight kill signals with token families:
    - `NEG_INFINITE_SET`
    - `NEG_COMMUTATIVE_ASSUMPTION`
    - `NEG_CLASSICAL_TIME`
  - `park_set` retains ten parked items with tag mix:
    - `NEAR_REDUNDANT` x `7`
    - `PROBE_PRESSURE` x `3`
  - `reject_log` retains sixteen reject rows with tag mix:
    - `NEAR_REDUNDANT` x `7`
    - `SCHEMA_FAIL` x `6`
    - `PROBE_PRESSURE` x `3`
  - all `18` `sim_promotion_status` entries are `PARKED`
  - retained semantic ids split across `A_` and `Z_` namespace prefixes

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/sequence_state.json`
- sha256: `524a7ed451d9307044988ac629b76afe3ea6247c330efb4c3a8a7d7099d8bfb3`
- size bytes: `92`
- source class: full run sequence ledger
- sequence maxima:
  - `A0 9`
  - `A1 8`
  - `A2 0`
  - `B 8`
  - `SIM 12`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/a1_inbox/sequence_state.json`
- sha256: `97abc2a63ff98b8381d8c224b0ec54121c822d93f5647f0da6493ad1e5307757`
- size bytes: `34`
- source class: inbox-local A1 sequence ledger
- retained marker:
  - `RUN_QIT_AUTORATCHET_0005|A1 -> 8`
- relation to root sequence ledger:
  - root and inbox ledgers are not identical JSON shapes
  - both preserve the same terminal A1 sequence max of `8`

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/events.jsonl`
- sha256: `0be6e705db74d1a452adc908db54691cb3e24fbab28461b0083af48012a5061d`
- size bytes: `14700`
- line count: `9`
- source class: compact autoratchet event ledger
- event markers:
  - explicit request event rows:
    - `a1_strategy_request_emitted`: `1`
  - implicit retained result rows:
    - `8`
  - step values present:
    - `1`
  - referenced strategy packets:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000004_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000005_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000006_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000007_A1_TO_A0_STRATEGY_ZIP.zip`
    - `000008_A1_TO_A0_STRATEGY_ZIP.zip`
  - referenced export packets:
    - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000003_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000004_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000005_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000006_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000007_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000008_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `000009_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - referenced sim outputs total: `12`
  - retained digest diversity:
    - `8` distinct strategy digests
    - `8` distinct export content digests
    - `5` distinct export structural digests
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
  - pass 3:
    - `accepted 11`
    - `parked 4`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 7`
  - pass 4:
    - `accepted 11`
    - `parked 0`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 10`
  - pass 5:
    - `accepted 7`
    - `parked 0`
    - `rejected 0`
    - `unresolved_promotion_blocker_count 12`
  - pass 6:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 14`
  - pass 7:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 16`
  - pass 8:
    - `accepted 3`
    - `parked 2`
    - `rejected 2`
    - `unresolved_promotion_blocker_count 18`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/soak_report.md`
- sha256: `37cf9a7f1b4a0289d92f1eb50c9cb629b0fa8d610c52ddce3f7d89c70605f48d`
- size bytes: `14890`
- source class: human-readable soak report
- report markers:
  - `cycle_count 1`
  - `accepted_total 3`
  - `parked_total 2`
  - `rejected_total 2`
  - `stop_reason MAX_STEPS`
  - top failure tags:
    - `SCHEMA_FAIL 3`
- retained event texture:
  - the last-event window preserves eight retained result rows over strategy packets `000001` through `000008`
  - rows 3 and 4 show the high-yield semantic expansion:
    - `accepted 11`
    - `parked 4` then `0`
    - `rejected 0`
  - the final three retained rows all show `accepted 3`, `parked 2`, `rejected 2`

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/zip_packets`
- source class: embedded packet lattice
- file count: `37`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `8`
  - `A1_TO_A0_STRATEGY_ZIP`: `8`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `8`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `12`
- embedded strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> eb9d790b4b033762ea02d29a5ad221bf6be27aec404a51673e5eb449782332ad`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 489a6ee34ed3fb2791666665ea9eb90527337e4d8dd63dd673f9b3ac7916a35a`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 220db8060a99e3f73da243fbb49eaee6682c171b77b7607dd836e03bde813b77`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> 1c4648aa334209d75966aef7e2f4adddb9e946b81244d988776539ad80b8c139`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 840f2cf6557492712b4445e32c37fa62bb6f3c649f97316067895d8bb86095a2`
  - `000006_A1_TO_A0_STRATEGY_ZIP.zip -> ccad32fc8fb6498a9dc4ee492825c7f2991c3908a8b9d2cffb559231d1557de3`
  - `000007_A1_TO_A0_STRATEGY_ZIP.zip -> 8fc53723947b9041af3edef905c795d5a88ed732f62b0c388ee416e22e2fb353`
  - `000008_A1_TO_A0_STRATEGY_ZIP.zip -> 5065a1efb6c1c27212309ddd7771bd2f2cfd955c58a4306cfd352f96d39eaae6`

### Source 10
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0005/a1_inbox/consumed`
- source class: fully consumed strategy residue
- file count: `8`
- consumed strategy packet hashes:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip -> c810ce7dac03c3190351b55a32a70a316806fe1da77f6d4c9e8d89d92229338d`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip -> 4eb04a33d3db9fa5fd0e83bd4548a395c004dba727bb0b3dcc8cbb478eef3783`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip -> 7e403a3e325508e6e5a38340d48e3cda74b1faec97738e17bf0431abea72d744`
  - `000004_A1_TO_A0_STRATEGY_ZIP.zip -> 537643959d16dc3afbf549734a0d143848552157668ce48f899b9c4e0a428444`
  - `000005_A1_TO_A0_STRATEGY_ZIP.zip -> 06f59d706c24148978d80b301da99f9bc326e6e147c4b96d640fb0758d6305d2`
  - `000006_A1_TO_A0_STRATEGY_ZIP.zip -> c9d5bf39ecc1949bf49bc6b1fe29c1fbbe2c7798a8d5accf2fd6178a12a79912`
  - `000007_A1_TO_A0_STRATEGY_ZIP.zip -> 52c16dded174fbc986a89f9c497ddba0103bf33cfc245964d8859de5b0fc5c5c`
  - `000008_A1_TO_A0_STRATEGY_ZIP.zip -> 431d4849e214d13e1579b0ce8e871a5ddef66d927b176933d20823202b6b59f8`
- lane relation to embedded strategy packets:
  - same eight filenames appear in both consumed and embedded lanes
  - all eight same-name pairs differ byte-for-byte
  - no live unconsumed strategy packets remain in `a1_inbox/`

## 3) Structural Map Of The Sources
### Segment A: queue-drained eight-pass autoratchet run with expanded sim lane
- source anchors:
  - run root inventory
  - `a1_inbox/consumed/`
  - `zip_packets/`
- source role:
  - preserves a direct autoratchet run captured after eight strategy packets were consumed, with a larger SIM output lane than the prior `0004` run
- strong markers:
  - eight consumed strategy packets survive
  - no live strategy packet files remain in `a1_inbox/`
  - `SIM_TO_A0_SIM_RESULT_ZIP` count rises to `12`

### Segment B: one-step headline over eight retained passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves strong step compression where eight retained result passes collapse into one nominal completed step
- strong markers:
  - `steps_completed 1`
  - `events.jsonl` keeps eight result-shaped rows after the initial request row
  - all retained result rows use step value `1`

### Segment C: digest-collapse summary over multi-digest history
- source anchors:
  - `summary.json`
  - `events.jsonl`
- source role:
  - preserves a collapse of digest diversity in the headline summary
- strong markers:
  - summary records `unique_strategy_digest_count 1`
  - summary records both export digest counts as `1`
  - retained result rows preserve `8` distinct strategy digests, `8` export content digests, and `5` export structural digests

### Segment D: semantic expansion under a flat final headline
- source anchors:
  - `summary.json`
  - `state.json`
  - `events.jsonl`
- source role:
  - preserves a larger semantic expansion than the unchanged final headline suggests
- strong markers:
  - summary headline is unchanged from `0004`
  - state expands to `evidence_pending_len 8`, `term_registry_len 8`, and `sim_results_len 12`
  - retained semantic families now include `one`, `trace_one`, and `CPTP_channel`

### Segment E: namespace drift and probe-pressure residue
- source anchors:
  - `state.json`
  - `soak_report.md`
- source role:
  - preserves a mixed naming regime and a new pressure class inside the same run family
- strong markers:
  - evidence keys and sim ids split across `A_` and `Z_` prefixes
  - `PROBE_PRESSURE` appears in both park and reject residue
  - `NEG_CLASSICAL_TIME` enters the kill-log token family

### Segment F: same-name strategy-family instability across eight pairs
- source anchors:
  - `zip_packets/`
  - `a1_inbox/consumed/`
- source role:
  - preserves a full eight-packet family where filename identity is never enough to recover byte identity
- strong markers:
  - same names `000001` through `000008` exist in both lanes
  - all eight consumed-versus-embedded pairs diverge byte-for-byte

