# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION NOTE
Batch: `BATCH_A2MID_archive_compact_test_lane_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction set

### CP1) Stale queued packet target vs live packet-zip child existence
Pole A:
- the queued next step still pointed at `TEST_A1_PACKET_ZIP`

Pole B:
- the live ledger already contains `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`

Preserved read:
- queue text can lag behind the live ledger and must not force duplicate reduction

### CP2) Multiple corrective nominations vs live child existence
Pole A:
- successive corrections could still point at `REAL_A1`, resume, state-transition, `PACKET_E2E_001`, or `PACKET_REQ_001` parents as unresolved compact targets

Pole B:
- the live ledger already contains direct children for all of those parents

Preserved read:
- even reasonable corrections become stale if they do not re-check the live ledger before promotion

### CP3) Earlier compact-family closure vs remaining compact-test work
Pole A:
- packet, deterministic, `REAL_A1`, resume, state-transition, and earlier `v2_zipv2` packet-bootstrap families now all have direct children

Pole B:
- the compact deep-archive test lane is still not closed

Preserved read:
- local family closure does not equal compact test-lane completion

### CP4) Sole remaining `REPLAY_001` parent vs false residual plurality
Pole A:
- stale continuation momentum can keep the lane looking like a multi-sibling routing problem

Pole B:
- the live ledger now leaves only one unresolved compact parent in this slice:
  - `V2_ZIPV2_REPLAY_001`

Preserved read:
- once sibling closure finishes, the routing problem collapses to the sole remaining parent rather than an open choice set

### CP5) Live-ledger routing vs inherited motion
Pole A:
- inherited motion could keep the worker stepping through already-childed packet, `REAL_A1`, state-transition, or earlier `v2_zipv2` siblings

Pole B:
- the current ledger points to `REPLAY_001` as the only remaining unresolved compact-test parent in this lane

Preserved read:
- routing must follow the current ledger, not inherited motion
