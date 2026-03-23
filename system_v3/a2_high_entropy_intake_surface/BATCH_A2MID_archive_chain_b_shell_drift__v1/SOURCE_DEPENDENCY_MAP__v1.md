# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_chain_b_shell_drift__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- direct sibling anchor:
  - `BATCH_A2MID_archive_chain_a_continuation_hashsplit__v1`
- predecessor anchor:
  - `BATCH_A2MID_archive_test_resume_stub_leakage__v1`

## Bounded Dependency Reads
- dependency group 1:
  - two executed transitions with queued third continuation
  - basis:
    - parent summary/manifest executed-spine notes
    - `events.jsonl`
    - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- dependency group 2:
  - replay attribution versus `needs_real_llm true`
  - basis:
    - `summary.json`
    - parent manifest notes
- dependency group 3:
  - summary/soak/sequence count three versus only two executed transitions
  - basis:
    - `summary.json`
    - `soak_report.md`
    - `sequence_state.json`
    - `events.jsonl`
    - `state.json`
- dependency group 4:
  - summary/state final hash versus last executed event endpoint, with queued third packet using final hash
  - basis:
    - `summary.json`
    - `state.json.sha256`
    - `events.jsonl`
    - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- dependency group 5:
  - second-step schema fail and blank target negative-class correlation
  - basis:
    - `events.jsonl`
    - `state.json`
    - `zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
- dependency group 6:
  - second-step `S0002` proposal versus mixed final survivor carryover
  - basis:
    - `state.json`
    - `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
- dependency group 7:
  - mixed-suffix duplicate file family and empty `zip_packets 2/` shell as packaging residue
  - basis:
    - parent manifest top-level entries
    - parent duplicate-file and empty-residue notes
- dependency group 8:
  - archived event rows still pointing to live-runtime paths
  - basis:
    - parent notes
    - `events.jsonl`

## Non-Dependencies
- no raw archive run reread was needed
- no mutation parent or later archive families were reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs

