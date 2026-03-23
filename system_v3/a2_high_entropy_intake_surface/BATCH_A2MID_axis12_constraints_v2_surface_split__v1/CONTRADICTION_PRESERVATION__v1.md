# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis12_constraints_v2_surface_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Local surface versus admitted descendant
- preserved contradiction:
  - the local surface emits evidence under its own SIM_ID
  - the repo-held pack omits that SIM_ID but admits `V2` under the same runner hash
- why preserved:
  - code-hash continuity and SIM_ID continuity remain different claims

### C2) Local four-layer surface versus descendant edge subset
- preserved contradiction:
  - the local surface stores four metric layers
  - the admitted `V2` descendant keeps only a narrower edge subset
- why preserved:
  - descendant admission does not erase surface-shape divergence

### C3) Same hash versus `seni` divergence
- preserved contradiction:
  - the local surface and `V2` share one runner hash
  - they still diverge on stored `seni` behavior for `SEQ03/SEQ04`
- why preserved:
  - provenance continuity does not force identical stored behavior

### C4) Shared axis1 profile versus opposite axis2 orientation
- preserved contradiction:
  - `SEQ03` and `SEQ04` share both within-pair activations
  - their worst axis2 failures point in opposite orientations
- why preserved:
  - shared asymmetric class does not erase internal orientation split

### C5) Balanced class versus unresolved pair
- preserved contradiction:
  - `SEQ01` and `SEQ02` share the same stored counts
  - the family still keeps them as distinct sequences
- why preserved:
  - the current metric layer does not settle the balanced pair semantically

## Quarantine markers
- quarantine marker:
  - `LOCAL_SURFACE_AS_REPOTOP_ADMITTED_VIA_SHARED_HASH`
- quarantine marker:
  - `V2_AS_FULL_LOCAL_METRIC_SURFACE`
- quarantine marker:
  - `SAME_HASH_AS_BEHAVIORAL_IDENTITY`
- quarantine marker:
  - `SEQ03_SEQ04_AS_ONE_UNDIFFERENTIATED_ASYMMETRIC_CLASS`
- quarantine marker:
  - `BALANCED_PAIR_AS_SEMANTICALLY_RESOLVED`
