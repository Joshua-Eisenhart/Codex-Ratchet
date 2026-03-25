# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_FOUNDATION_BATCH_PASS`
Batch scope: archive-only intake of `RUN_FOUNDATION_BATCH_0001`, bounded to its retained control files, packet lattice, event ledger, and inbox residue
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/summary.json`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/HARDMODE_METRICS.json`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/state.json`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/state.json.sha256`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/sequence_state.json`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/events.jsonl`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/soak_report.md`
  - retained subtree inventories for:
    - `zip_packets/`
    - `a1_inbox/consumed/`
- reason for bounded family batch:
  - the previous deep-archive run-root batch identified `RUN_FOUNDATION_BATCH_0001` as the densest preserved parent campaign with direct derivative bundles nearby
  - this pass stays inside the run directory itself and does not descend into sibling bundles or other run families
  - the goal is to preserve the run’s historical packet grammar, state/control contradictions, and demotion lineage without treating the archived run body as live authority
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/summary.json`
- sha256: `b6ed6a42f325bfcdce6a0ba9ce5cdab845fb617ee5f15bba2b23f59e9947516c`
- size bytes: `852`
- source class: top-line run summary

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/HARDMODE_METRICS.json`
- sha256: `18ea9c1cb348d2533265c6dd48e54e355c82959b0132d11731080bea015a2986`
- size bytes: `1075`
- source class: cumulative run metrics capsule

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/state.json`
- sha256: `e3d0b4fd7c342a331281b99796e81aea2349abb9fc37f06e6b1b5b8eff0c331d`
- size bytes: `4087032`
- source class: retained terminal run state

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/state.json.sha256`
- source class: detached state integrity sidecar
- integrity result:
  - declared hash matches actual `state.json` sha256

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/sequence_state.json`
- sha256: `62fb3e6fae631612a22e16d43a555d958444795ab50cc70e41900a86b38fafb9`
- size bytes: `101`
- source class: source-lane sequence counter summary

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/events.jsonl`
- sha256: `855f229427aef32b67c21baf10638d6b57d1ce3651984031bb1833b9e3f85edd`
- size bytes: `943243`
- line count: `265`
- source class: event ledger

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/soak_report.md`
- sha256: `1f41e07b7e76039d05d8acb503eb981426ba0808b5f11e6d69b9f412524f9224`
- size bytes: `72037`
- source class: human-readable run report

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/zip_packets`
- file count: `2365`
- source class: packet lattice
- retained packet kinds:
  - `A1_TO_A0_STRATEGY_ZIP`: `265`
  - `A0_TO_B_EXPORT_BATCH_ZIP`: `264`
  - `B_TO_A0_STATE_UPDATE_ZIP`: `263`
  - `SIM_TO_A0_SIM_RESULT_ZIP`: `1571`
  - `A0_TO_A1_SAVE_ZIP`: `2`

### Source 9
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/LEGACY__MIGRATED__FROM_RUN_ROOT/bootpack_b_kernel_v1__runs__/RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed`
- file count: `267`
- source class: retained consumed-strategy residue
- visible numbering blocks:
  - `000001..000011`
  - `100012..100041`
  - `200042..200081`
  - `300082..300181`
  - `400182..400267`

## 3) Structural Map Of The Sources
### Segment A: top-level run capsule
- source anchors:
  - full top-level inventory of `RUN_FOUNDATION_BATCH_0001`
- source role:
  - defines the archived run as a compact control shell around one large state file and two large transport subtrees
- strong markers:
  - top-level entries are exactly:
    - `HARDMODE_METRICS.json`
    - `a1_inbox/`
    - `events.jsonl`
    - `sequence_state.json`
    - `soak_report.md`
    - `state.json`
    - `state.json.sha256`
    - `summary.json`
    - `zip_packets/`
  - there is no retained `sim/` directory in the archived run body

### Segment B: summary-and-metrics control surface
- source anchors:
  - sources 1-2
- source role:
  - preserves the top-line read of the run while also exposing the first contradiction layer
- strong markers:
  - summary: `steps_completed 60`, `accepted_total 840`, `rejected_total 0`, `parked_total 0`, `stop_reason MAX_STEPS`, `sim_registry_count 1571`, `unresolved_promotion_blocker_count 519`
  - metrics: `canonical_ledger_len 263`, `survivor_count 3537`, `sim_registry_count 1571`, `zip_packet_count 2365`, `killed_count 519`, `pending_count 223`
  - metrics promotion counts: `ACTIVE 1052`, `PARKED 519`
  - metrics cumulative reject tags: `SCHEMA_FAIL 85`, `SHADOW_ATTEMPT 56`, `NEAR_REDUNDANT 5`, `UNDEFINED_TERM_USE 7`

### Segment C: hash-bound terminal state surface
- source anchors:
  - sources 3-5
- source role:
  - preserves the end-state as a large, hash-bound artifact plus compact counters
- strong markers:
  - `state.json.sha256` matches the actual `state.json` digest and also matches the summary `final_state_hash`
  - state summary counts:
    - `accepted_batch_count 263`
    - `canonical_ledger_len 263`
    - `survivor_order_len 3537`
    - `term_registry_len 723`
    - `derived_only_terms_len 47`
    - `kill_log_len 519`
    - `reject_log_len 153`
    - `park_set_len 12`
    - `evidence_pending_len 223`
    - `sim_registry_len 1571`
    - `sim_results_len 1571`
  - `active_megaboot_id`, `active_megaboot_sha256`, and `active_ruleset_sha256` are all empty strings
  - sequence counters:
    - `A0 265`
    - `A1 265`
    - `A2 0`
    - `B 263`
    - `SIM 1571`

### Segment D: event-ledger transport surface
- source anchors:
  - source 6
- source role:
  - records how the campaign progressed step-by-step and what the archived event stream still points to
- strong markers:
  - total event lines: `265`
  - first line is a special `a1_strategy_request_emitted` record
  - subsequent event rows preserve:
    - export digests
    - state transition digests
    - packet paths
    - unresolved blocker counts
    - lists of satisfied sim ids per step
  - first result rows include early `SCHEMA_FAIL` and parked/rejected movement
  - final rows show step `60`, `accepted 14`, `rejected 0`, `parked 0`, and `unresolved_promotion_blocker_count 519`

### Segment E: packet lattice surface
- source anchors:
  - source 8
- source role:
  - preserves the exchange grammar of the run more directly than any prose file
- strong markers:
  - packet indices span `1..1571`
  - SIM packets dominate numerically with `1571` results
  - strategy requests and A0 sequence counts line up at `265`
  - B-state returns stop earlier at `263`
  - only `2` `A0_TO_A1_SAVE_ZIP` packets are retained across the whole campaign

### Segment F: inbox residue surface
- source anchors:
  - source 9
- source role:
  - shows the archive preserved a second, consumed copy-line of A1 strategy traffic rather than only the normalized packet lattice
- strong markers:
  - `267` consumed strategy zips remain under `a1_inbox/consumed`
  - numbering jumps across five prefixed blocks instead of one clean monotonic series
  - consumed-strategy count does not equal the `265` strategy packets in `zip_packets/`

### Segment G: missing-evidence surface
- source anchors:
  - top-level directory inventory
  - event and soak report path references
- source role:
  - preserves an archival contradiction: the run still references a richer runtime tree than the archive retained
- strong markers:
  - event rows and soak-report entries reference `sim/sim_evidence_*` files under the original runtime path
  - the archived run directory has no `sim/` subtree
  - the archive therefore retains transport and digest traces more completely than underlying sim evidence bodies

## 4) Source-Class Read
- best classification:
  - archive-only long-run foundation campaign packet with hash-bound terminal state, dense event/packet traffic, and preserved inbox residue
- useful as:
  - historical lineage for how a foundation batch run combined A1 strategy traffic, B export/state updates, and large SIM result ladders
  - archive evidence that throughput and artifact density can coexist with unresolved promotion blockers and not-ready sim status
  - parent structural reference for nearby progress-bundle derivatives
- not best classified as:
  - active runtime state
  - complete retained sim evidence
  - current policy authority
- possible downstream consequence:
  - the next bounded pass should process `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE` to compare the parent run against its derived progress export surface
