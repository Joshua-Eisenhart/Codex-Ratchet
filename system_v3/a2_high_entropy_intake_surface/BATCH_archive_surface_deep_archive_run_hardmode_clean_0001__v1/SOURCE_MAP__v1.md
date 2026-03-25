# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_hardmode_clean_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_HARDMODE_CLEAN_PASS`
Batch scope: archive-only intake of `RUN_HARDMODE_CLEAN_0001`, bounded to the direct run root, hardmode metrics, core run-state surfaces, the embedded packet lattice, and the consumed strategy lane
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct run root:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001`
  - core run-state surfaces:
    - `summary.json`
    - `state.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `soak_report.md`
    - `HARDMODE_METRICS.json`
    - `zip_packets/`
  - retained input residue:
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - this pass processes only the large direct run `RUN_HARDMODE_CLEAN_0001` and does not reopen sibling runs
  - the archive value is a large-scale "hardmode clean" run that preserves clean parked/reject counters while still keeping a heavy kill/pending/promoted-state burden
  - the run is also useful for packet-lineage history because its consumed and embedded strategy lanes share numbering structure but mostly not identical bytes
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_QIT_AUTORATCHET_0001`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001`
- source class: large direct run root
- total files: `2208`
- total directories: `3`
- top-level entries:
  - `HARDMODE_METRICS.json`
  - `a1_inbox`
  - `events.jsonl`
  - `soak_report.md`
  - `state.json`
  - `state.json.sha256`
  - `summary.json`
  - `zip_packets`
- notable absences:
  - no wrapper README
  - no `sequence_state.json`
  - no `sim/` directory

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/summary.json`
- sha256: `015f77aa6f97a125ca669412cfe75f813b36153fa98744d286fc2497e82ecd49`
- size bytes: `856`
- source class: direct final snapshot summary
- summary markers:
  - `run_id RUN_HARDMODE_CLEAN_0001`
  - `steps_completed 100`
  - `accepted_total 1400`
  - `parked_total 0`
  - `rejected_total 0`
  - `sim_registry_count 1320`
  - `unresolved_promotion_blocker_count 440`
  - `final_state_hash 80d036951d8d7226cfce4fd80755f0553bfd1946920dcb4463c3530853d77a3f`
- promotion totals by tier:
  - `T1_COMPOUND pass 440 fail 440`
  - `T2_OPERATOR pass 220`
  - `T3_STRUCTURE pass 220`

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/state.json`
- sha256: `80d036951d8d7226cfce4fd80755f0553bfd1946920dcb4463c3530853d77a3f`
- size bytes: `3482068`
- source class: direct final snapshot state
- compact state markers:
  - `accepted_batch_count 220`
  - `canonical_ledger_len 220`
  - `derived_only_terms_len 47`
  - `evidence_pending_len 220`
  - `evidence_tokens_len 1320`
  - `interaction_counts_len 880`
  - `kill_log_len 440`
  - `park_set_len 0`
  - `reject_log_len 0`
  - `sim_promotion_status_len 1320`
  - `sim_registry_len 1320`
  - `sim_results_len 1320`
  - `survivor_order_len 3082`
  - `term_registry_len 660`
- retained state markers:
  - `evidence_pending` is a dictionary with `220` canonical keys from `S_CANON_A_0001` through `S_CANON_A_0220`
  - `kill_log` contains `440` distinct negative-branch kill tokens
  - no parked packets and no reject-log entries despite the pending and kill burden

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/state.json.sha256`
- source class: state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256
  - declared hash matches `summary.json` final state hash

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/HARDMODE_METRICS.json`
- sha256: `c9131bcc773c75a2a1f525779871083988a8b0a82b6b6c414b5325f7cc68ed99`
- size bytes: `968`
- source class: hardmode aggregate metrics
- metric markers:
  - `active_count 2422`
  - `canonical_ledger_len 220`
  - `term_registry_count 660`
  - `interaction_counts_count 880`
  - `kill_log_count 440`
  - `killed_count 440`
  - `pending_count 220`
  - `survivor_count 3082`
  - `sim_results_total 1320`
  - `zip_packet_count 1981`
  - promotion status counts:
    - `ACTIVE 880`
    - `PARKED 440`
  - sim family counts:
    - `BASELINE 220`
    - `BOUNDARY_SWEEP 220`
    - `ADVERSARIAL_NEG 440`
    - `PERTURBATION 220`
    - `COMPOSITION_STRESS 220`

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/events.jsonl`
- sha256: `3af55b4ab102ff20c95d273c51e0ab5c5dc0b282b0ff118963585cff6e72869a`
- size bytes: `783945`
- line count: `221`
- source class: large direct event ledger
- event markers:
  - event kinds:
    - `a1_strategy_request_emitted`: `1`
    - `step_result`: `220`
  - event step range:
    - minimum step: `1`
    - maximum step: `120`
    - unique step values: `120`
    - step values repeated more than once: `100`
  - referenced strategy packets: `220`
  - referenced export packets: `220`
  - referenced sim result packet count: `1320`
  - persistent path drift:
    - event rows still point to runtime-path `sim/sim_evidence_*` files that are not retained inside the archive object

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/soak_report.md`
- sha256: `068f3f061da21ab2aa9229ea36ce710fd1388c9653b4def8d2f1df53496e9b93`
- size bytes: `71448`
- source class: human-readable soak report
- report markers:
  - `cycle_count 100`
  - `accepted_total 1400`
  - `parked_total 0`
  - `rejected_total 0`
  - `stop_reason MAX_STEPS`
  - top failure tag set: `NONE`

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/zip_packets`
- source class: embedded packet lattice
- file count: `1981`
- packet kind counts:
  - `A0_TO_A1_SAVE_ZIP`: `1`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `220`
  - `A1_TO_A0_STRATEGY_ZIP`: `220`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `220`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `1320`

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_HARDMODE_CLEAN_0001/a1_inbox/consumed`
- source class: consumed strategy lane
- file count: `220`
- filename range:
  - first packet: `400001_A1_TO_A0_STRATEGY_ZIP.zip`
  - last packet: `400220_A1_TO_A0_STRATEGY_ZIP.zip`
- lane relation to embedded strategy packets:
  - consumed lane count equals embedded strategy-packet count: `220`
  - pairwise same-position hash comparison matches for `1` packet only and diverges for `219`
  - sample equal pair:
    - consumed `400001...` hash `1e16644121b1e0c539625d68837255493fc343f2e65b9b353a95873f1e1c1db4`
    - embedded `000001...` hash `1e16644121b1e0c539625d68837255493fc343f2e65b9b353a95873f1e1c1db4`
  - sample divergent pair:
    - consumed `400220...` hash `79e039833db13ac2b0ee4d181d40a660c6b2198c1d4013c8fb5b22c951e6a45f`
    - embedded `000220...` hash `ec1f316020cabb495431534349116a754cba2d53295beb2cc5ea777bb97e3eec`

## 3) Structural Map Of The Sources
### Segment A: hardmode-clean direct run
- source anchors:
  - direct run root inventory
  - `summary.json`
  - `soak_report.md`
- source role:
  - preserves a large direct run with no wrapper bundle and no replay README
- strong markers:
  - `steps_completed 100`
  - `accepted_total 1400`
  - `parked_total 0`
  - `rejected_total 0`
  - hardmode-specific metrics surface retained alongside core state

### Segment B: clean-window versus burdened state
- source anchors:
  - `summary.json`
  - `state.json`
  - `HARDMODE_METRICS.json`
- source role:
  - preserves the split between window-clean transport counts and heavy retained burden in state
- strong markers:
  - no parked packets and no rejected packets
  - `kill_log_len 440`
  - `evidence_pending_len 220`
  - hardmode promotion status counts still include `PARKED 440`

### Segment C: event-regime mismatch
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- source role:
  - preserves a counting-regime mismatch between top-line cycle reporting and retained event rows
- strong markers:
  - summary and soak report say `100` cycles/steps
  - event ledger contains `220` result rows
  - event step field ranges across `120` unique step values

### Segment D: dual strategy lanes
- source anchors:
  - `a1_inbox/consumed/`
  - `zip_packets/`
- source role:
  - preserves two strategy-packet lanes with parallel cardinality but mostly non-identical bytes
- strong markers:
  - consumed lane uses `400001`-`400220`
  - embedded transport lane uses `000001`-`000220`
  - only the first aligned pair matches byte-for-byte

### Segment E: evidence-light large archive
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
  - run root inventory
- source role:
  - preserves large state and transport residue without the local evidence bodies it references
- strong markers:
  - repeated runtime-path `sim/sim_evidence_*` references remain
  - no `sim/` directory is retained

