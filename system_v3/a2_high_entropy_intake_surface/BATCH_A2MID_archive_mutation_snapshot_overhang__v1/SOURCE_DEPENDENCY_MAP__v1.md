# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent Batch
- primary parent:
  - `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
- parent artifacts used:
  - `SOURCE_MAP__v1.md`
  - `CLUSTER_MAP__v1.md`
  - `TENSION_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `MANIFEST.json`

## Comparison Anchors
- direct predecessor anchor:
  - `BATCH_A2MID_archive_chain_b_shell_drift__v1`
- nearby archive-test anchor:
  - `BATCH_A2MID_archive_test_resume_stub_leakage__v1`

## Bounded Dependency Reads
- dependency group 1:
  - one executed mutation step with one strategy, one export, one Thread-S snapshot, and two SIM returns
  - basis:
    - `summary.json`
    - `state.json`
    - `sequence_state.json`
    - `events.jsonl`
    - `zip_packets/`
- dependency group 2:
  - summary/state final hash versus the only executed event endpoint
  - basis:
    - `summary.json`
    - `state.json.sha256`
    - `events.jsonl`
- dependency group 3:
  - zero parked packets versus two `PARKED` promotion states and unresolved blockers
  - basis:
    - `summary.json`
    - `soak_report.md`
    - `state.json`
- dependency group 4:
  - snapshot `EVIDENCE_PENDING` residue versus empty final `evidence_pending`
  - basis:
    - `state.json`
    - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
- dependency group 5:
  - export/snapshot `KILL_IF ... NEG_NEG_BOUNDARY` residue versus empty final `kill_log`
  - basis:
    - `zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
    - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
    - `state.json`
    - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
    - `zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`
- dependency group 6:
  - exact duplicate ` 2` file family and empty residue directories as packaging noise
  - basis:
    - parent duplicate-file notes
    - parent empty-directory notes
    - `MANIFEST.json`
- dependency group 7:
  - archived event schema and live-runtime path leakage
  - basis:
    - `events.jsonl`
    - parent path-drift notes

## Non-Dependencies
- no raw archive run reread was needed
- no sibling `V2_ZIPV2_PACKET_E2E_001` or later archive families were reopened
- no active `system_v3/a2_state` surfaces were used as authority inputs
