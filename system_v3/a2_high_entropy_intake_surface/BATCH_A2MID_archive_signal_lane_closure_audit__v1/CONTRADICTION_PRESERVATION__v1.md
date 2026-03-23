# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION NOTE
Batch: `BATCH_A2MID_archive_signal_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction set

### CP1) Signal-lane closure vs residual deep-archive work
Pole A:
- the `RUN_SIGNAL` lane is now child-complete across raw `0002` through raw `0005` plus `0005_bundle`

Pole B:
- deep-archive re-entry is still not complete

Preserved read:
- lane closure does not equal deep-archive completion

### CP2) Rich repaired signal surfaces vs best next target elsewhere
Pole A:
- raw `0005` and `0005_bundle` preserve the richest repaired signal-side packets

Pole B:
- the strongest next target is still outside that lane

Preserved read:
- richer local detail does not by itself justify reopening a closed lane

### CP3) Existing sibling child vs unresolved sibling target
Pole A:
- `TEST_A1_PACKET_EMPTY` already has a direct A2-mid child

Pole B:
- `TEST_A1_PACKET_ZIP` does not

Preserved read:
- sibling support increases value for the unchilded partner rather than eliminating it

### CP4) Compact packet-loop seam vs broader replay and state-transition families
Pole A:
- `TEST_A1_PACKET_ZIP` is compact and packet-facing

Pole B:
- `TEST_REAL_A1_002`, `TEST_RESUME_001`, and the state-transition family carry broader retained contradictions

Preserved read:
- compactness plus sibling-anchor leverage can outrank broader unresolved families

### CP5) Live ledger routing vs stale continuation momentum
Pole A:
- stale queue logic could keep descending by run number or by recently touched family

Pole B:
- the live ledger shows that family is already closed and points to a different unresolved pool

Preserved read:
- routing must follow current ledger state, not inherited motion
