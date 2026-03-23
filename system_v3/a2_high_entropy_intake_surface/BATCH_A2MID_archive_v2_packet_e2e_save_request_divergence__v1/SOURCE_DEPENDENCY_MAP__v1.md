# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- packet-identity anchor:
  - `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
- mutation-overhang anchor:
  - `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`

## Bounded Dependency Reads
- dependency group 1:
  - one executed ZIPv2 packet cycle followed by an external A1 save-request handoff
  - basis:
    - `summary.json`
    - `events.jsonl`
    - `soak_report.md`
    - `zip_packets/000002_A0_TO_A1_SAVE_ZIP.zip`
- dependency group 2:
  - final retained closure surfacing only through the save-request row
  - basis:
    - `summary.json`
    - `state.json.sha256`
    - `events.jsonl`
- dependency group 3:
  - zero parked packets versus one `PARKED` promotion state, one unresolved blocker, and absent canonical ledger rows
  - basis:
    - `summary.json`
    - `soak_report.md`
    - `state.json`
- dependency group 4:
  - same-name retained versus consumed strategy packet divergence
  - basis:
    - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
    - parent divergence notes
- dependency group 5:
  - packet-facing residue richer than final bookkeeping
  - basis:
    - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `state.json`
- dependency group 6:
  - runtime-local event paths and missing `sequence_state.json`
  - basis:
    - `events.jsonl`
    - `zip_packets/`
    - parent missing-sequence notes

## Non-Dependencies
- no raw archive run reread was needed
- no sibling `V2_ZIPV2_PACKET_REQ_001` or later archive families were reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs
