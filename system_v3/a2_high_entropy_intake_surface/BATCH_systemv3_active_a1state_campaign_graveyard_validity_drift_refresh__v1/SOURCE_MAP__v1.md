# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a1state_campaign_graveyard_validity_drift_refresh__v1`
Extraction mode: `ACTIVE_A1STATE_CAMPAIGN_GRAVEYARD_VALIDITY_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## 1) Scope
- bounded live-source refresh over the drifted doctrine subset inside the earlier active `a1_state` campaign/graveyard-validity family
- purpose:
  - preserve the exact two live doctrine files that no longer match the earlier first-pass manifest
  - keep the earlier family batch intact as a historical snapshot
  - record where the entropy bridge campaign spine and the graveyard-first validity profile changed after the original pass

## 2) Source Set
- live drifted source members:
  - `system_v3/a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md`
  - `system_v3/a1_state/A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`
- unchanged members still preserved by the earlier family batch:
  - `A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
  - `A1_FIRST_ENTROPY_BROAD_RESCUE_PACK__v1.md`
  - `A1_FIRST_ENTROPY_ENGINE_CAMPAIGN__v1.md`
  - `A1_FIRST_ENTROPY_ENGINE_FAMILY__v1.md`
  - `A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md`
  - `A1_FIRST_SUBSTRATE_FAMILY_CAMPAIGN__v1.md`
  - `A1_NEGATIVE_CLASS_REGISTRY__v1.md`
  - `A1_RESCUE_AND_GRAVEYARD_OPERATORS__v1.md`
- comparison anchors:
  - `BATCH_systemv3_active_a1state_campaign_graveyard_validity_packet__v1/MANIFEST.json`
  - `BATCH_systemv3_active_a1state_integration_rosetta_meta_packet__v1/MANIFEST.json`

## 3) Why This Refresh Exists
- the queued reuse check failed because the earlier active campaign/graveyard-validity family manifest no longer matched live repo state
- drift count:
  - changed members: `2`
  - unchanged members from the earlier family: `8`
- this packet does not replace the earlier batch
- it preserves the earlier batch as a source-bound snapshot and adds the now-live doctrine delta surface beside it

## 4) Drifted Membership By Function
- `a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md`
  - old snapshot: `1282` lines / `56189` bytes
  - live source: `1283` lines / `56152` bytes
  - main live drift:
    - the file still functions as the accretive entropy bridge campaign spine rather than a clean single-claim doctrine
    - the live surface still retains rescue-pack injection, thermal/time split audit, helper-strip failure, planner-side helper suppression, cluster-rescue broadening, and late default admissibility routing
    - the drift looks like live thickening and reshaping around the same campaign spine, not a lane overthrow
- `a1_state/A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`
  - old snapshot: `424` lines / `18245` bytes
  - live source: `425` lines / `18321` bytes
  - main live drift:
    - the file still distinguishes scaffold proof from stronger graveyard-first validity mode
    - the entropy section still preserves the split between thin local bridge seed, broad exploratory graveyard validity, and negative evidence on isolated bookkeeping or single-term local routes
    - the drift again looks like slight thickening around the same validity doctrine, not a new validity regime

## 5) Grouped Read
- entropy bridge campaign refresh:
  - `A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md`
- graveyard validity refresh:
  - `A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`

## 6) Current Best Read
- the earlier active campaign/graveyard-validity batch remains historically useful, but it is not current on this two-file doctrine pair
- live drift is bounded:
  - executable distillation rules remain unchanged
  - broad rescue control remains unchanged
  - first entropy engine family and campaign scaffolds remain unchanged
  - direct entropy-structure campaign remains unchanged
  - first substrate campaign remains unchanged
  - negative class registry and rescue/graveyard operators remain unchanged
- the live pair still preserves the same high-level doctrine picture:
  - entropy bridge routing remains accretive and internally tensioned rather than cleanly collapsed
  - graveyard-first validity remains the stronger validity mode without becoming direct truth-promotion
  - broad exploratory graveyard work still matters without erasing thin local seed evidence

## 7) Notes
- no active source was mutated
- no older batch was rewritten
- this packet is a bounded refresh surface, not a retroactive normalization of the earlier active `a1_state` campaign/graveyard-validity family
