# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- direct sibling anchor:
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
- packet-floor anchor:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`

## Bounded Dependency Reads
- dependency group 1:
  - request-only ZIPv2 bootstrap with no executed lower-loop packet cycle
  - basis:
    - `summary.json`
    - `events.jsonl`
    - `soak_report.md`
    - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- dependency group 2:
  - packet-mode labeling versus no retained inbound strategy or strategy/export digests
  - basis:
    - `summary.json`
    - `a1_inbox/`
    - `zip_packets/`
- dependency group 3:
  - requested three steps versus one retained immediate handoff row
  - basis:
    - `summary.json`
    - `events.jsonl`
    - `soak_report.md`
- dependency group 4:
  - inert final state with lexical/bootstrap shells still populated
  - basis:
    - `state.json`
    - `state.json.sha256`
- dependency group 5:
  - outer save summary state hash versus embedded base-strategy zero hash and placeholder self-audit
  - basis:
    - `state.json`
    - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
- dependency group 6:
  - runtime-local event path leakage and missing `sequence_state.json`
  - basis:
    - `events.jsonl`
    - `zip_packets/`
    - `MANIFEST.json`

## Non-Dependencies
- no raw archive run reread was needed
- no sibling `V2_ZIPV2_REPLAY_001` or later archive families were reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs
