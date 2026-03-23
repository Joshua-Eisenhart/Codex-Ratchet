# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_replay_hashbridge_schemafail__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- direct ZIPv2 sibling anchor:
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- packet-e2e sibling anchor:
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`

## Bounded Dependency Reads
- dependency group 1:
  - two executed replay steps plus a queued third strategy packet
  - basis:
    - `summary.json`
    - `soak_report.md`
    - `events.jsonl`
    - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- dependency group 2:
  - count-three summary and soak surfaces versus two-step event retention
  - basis:
    - `summary.json`
    - `soak_report.md`
    - `events.jsonl`
- dependency group 3:
  - hidden hash bridges between step 1 and step 2, and between step 2 and final retained state
  - basis:
    - `events.jsonl`
    - `summary.json`
    - `state.json.sha256`
    - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- dependency group 4:
  - replay authorship versus real-LLM demand and empty inbox
  - basis:
    - `summary.json`
    - `a1_inbox/`
- dependency group 5:
  - step-2 `SCHEMA_FAIL` asymmetry across proposed `S0002` lanes and final survivors
  - basis:
    - `events.jsonl`
    - `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
    - `zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `zip_packets/000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `state.json`
- dependency group 6:
  - snapshot pending evidence and SIM kill-signal residue outrunning final bookkeeping
  - basis:
    - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `state.json`
- dependency group 7:
  - empty inbox residue, runtime-local event paths, and missing `sequence_state.json`
  - basis:
    - `a1_inbox/`
    - `events.jsonl`
    - `zip_packets/`
    - `MANIFEST.json`

## Non-Dependencies
- no raw archive run reread was needed
- no later heat-dump or non-ZIPv2 archive families were reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs
