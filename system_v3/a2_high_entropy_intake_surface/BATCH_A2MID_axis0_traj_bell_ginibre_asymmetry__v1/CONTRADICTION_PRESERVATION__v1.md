# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_A2MID_axis0_traj_bell_ginibre_asymmetry__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Preserved contradiction set
### C1) Bell versus Ginibre trajectory-negativity split
- preserved contradiction:
  - the same runner stores nonzero Bell trajectory negativity
  - the same runner stores zero Ginibre trajectory negativity
- why preserved:
  - initialization regime remains a live differentiator

### C2) Trajectory negativity versus positive final state
- preserved contradiction:
  - Bell begins in negative conditional entropy and carries nonzero trajectory negativity
  - both Bell branches end at positive final `S(A|B)`
- why preserved:
  - trajectory negativity and final-state negativity remain different claims

### C3) Small deltas versus init-qualified direction
- preserved contradiction:
  - sequence-order deltas remain small
  - their sign flips between Bell and Ginibre
- why preserved:
  - smallness does not erase init-qualified direction changes

### C4) Higher trajectory MI versus lower positive trajectory `S(A|B)`
- preserved contradiction:
  - Bell carries larger trajectory `MI`
  - Ginibre carries larger positive trajectory `S(A|B)` mean
- why preserved:
  - metric strength remains non-collinear in this family

### C5) Local evidence versus repo-top omission
- preserved contradiction:
  - the family is catalog-visible and locally evidenced
  - the repo-held top-level evidence pack omits the local `SIM_ID`
- why preserved:
  - local evidence and repo-top admission remain separate layers

## Quarantine markers
- quarantine marker:
  - `BELL_TRAJECTORY_NEGATIVITY_AS_NEGATIVE_FINAL_STATE`
- quarantine marker:
  - `SMALL_SEQUENCE_DELTAS_AS_INIT_INDEPENDENT_DIRECTION`
- quarantine marker:
  - `MI_AND_POSITIVE_SAGB_TRAJECTORY_MEANS_AS_CO_MOVING`
- quarantine marker:
  - `BELL_AND_GINIBRE_AS_ONE_REGIME_STORY`
- quarantine marker:
  - `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
