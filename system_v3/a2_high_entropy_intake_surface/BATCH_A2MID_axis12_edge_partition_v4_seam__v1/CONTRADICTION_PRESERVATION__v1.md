# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis12_edge_partition_v4_seam__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Local suite versus admitted descendant
- preserved contradiction:
  - the local suite emits evidence under its own SIM_ID
  - the repo-held pack omits that SIM_ID but admits `V4` under the same runner hash
- why preserved:
  - code-hash continuity and SIM_ID continuity remain different claims

### C2) Coarse edge partition versus finer endpoint order
- preserved contradiction:
  - `SEQ01/SEQ02` share one edge class and `SEQ03/SEQ04` share the other
  - endpoint metrics still differentiate members inside each class
- why preserved:
  - edge flags remain a coarse classifier, not a complete ordering model

### C3) Axis12 label versus global sign directionality
- preserved contradiction:
  - the family is organized by axis12 edge structure
  - sign `+1` still lowers entropy and raises purity across all sequences
- why preserved:
  - the sign layer remains materially active inside an axis12-labeled family

### C4) Fixed snapshot versus grid-scan descendant
- preserved contradiction:
  - the local suite fixes one parameter tuple
  - the admitted descendant scans a `3 x 3 x 3 x 3` grid
- why preserved:
  - descendant admission does not erase surface-shape divergence

### C5) Shared no-edge class versus stable `SEQ02` advantage
- preserved contradiction:
  - `SEQ01` and `SEQ02` share the same no-edge class
  - `SEQ02` is still locally best under both signs
- why preserved:
  - shared coarse class does not erase finer endpoint ordering

## Quarantine markers
- quarantine marker:
  - `LOCAL_SUITE_AS_REPOTOP_ADMITTED_VIA_SHARED_HASH`
- quarantine marker:
  - `EDGE_FLAGS_AS_FULL_ENDPOINT_ORDERING_MODEL`
- quarantine marker:
  - `AXIS12_FAMILY_AS_PURELY_AXIS12_STRUCTURAL_WITHOUT_SIGN_LAYER`
- quarantine marker:
  - `V4_AS_RENAMED_COPY_OF_LOCAL_SNAPSHOT`
- quarantine marker:
  - `ADJACENT_HARDEN_RUNNERS_AS_CURRENT_PAIRED_BATCH`
