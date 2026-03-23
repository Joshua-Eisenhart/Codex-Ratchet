# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a1state_entropy_control_pack_drift_refresh__v1`
Extraction mode: `ACTIVE_A1STATE_ENTROPY_CONTROL_PACK_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## 1) Scope
- bounded live-source refresh over the drifted bridge-support subset inside the earlier active `a1_state` entropy-control family
- purpose:
  - preserve the exact three live entropy bridge-support files that no longer match the earlier first-pass manifest
  - keep the earlier family batch intact as a historical snapshot
  - record where the colder-witness, helper-lift, and reformulation trio changed after the original pass

## 2) Source Set
- live drifted source members:
  - `system_v3/a1_state/A1_ENTROPY_BRIDGE_COLDER_WITNESS_PACK__v1.md`
  - `system_v3/a1_state/A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__v1.md`
  - `system_v3/a1_state/A1_ENTROPY_BRIDGE_REFORMULATION_PACK__v1.md`
- unchanged members still preserved by the earlier family batch:
  - `A1_ENTROPY_BRANCH_BUDGET_AND_MERGE_PACK__v1.md`
  - `A1_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__v1.md`
  - `A1_ENTROPY_BRIDGE_PATH_BUILD_PRIORITY_PACK__v1.md`
  - `A1_ENTROPY_CLUSTER_RESCUE_PACK__v1.md`
  - `A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
- comparison anchors:
  - `BATCH_systemv3_active_a1state_entropy_control_pack_family__v1/MANIFEST.json`
  - `BATCH_systemv3_active_a1state_entropy_support_pack_family__v1/MANIFEST.json`

## 3) Why This Refresh Exists
- the queued reuse check failed because the earlier active entropy-control family manifest no longer matched live repo state
- drift count:
  - changed members: `3`
  - unchanged members from the earlier family: `5`
- this packet does not replace the earlier batch
- it preserves the earlier batch as a source-bound March 9 snapshot and adds the now-live bridge-support delta surface beside it

## 4) Drifted Membership By Function
- `a1_state/A1_ENTROPY_BRIDGE_COLDER_WITNESS_PACK__v1.md`
  - old snapshot: `138` lines / `4611` bytes
  - live source: `139` lines / `4675` bytes
  - main live drift:
    - the file still enforces colder-witness and partition/correlation leadership before late alias bridge terms
    - it is now slightly thicker around the first audit and retained wrapper-status reading
    - the anti-reopening fence on direct work/rate/engine narration still holds
- `a1_state/A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__v1.md`
  - old snapshot: `80` lines / `2486` bytes
  - live source: `80` lines / `2442` bytes
  - main live drift:
    - the file still forbids lone colder helpers as valid leading branches
    - it remains the helper-plus-partition-plus-late-alias composition rule
    - the live surface is slightly tighter in wording, not a role-map overturn
- `a1_state/A1_ENTROPY_BRIDGE_REFORMULATION_PACK__v1.md`
  - old snapshot: `133` lines / `4198` bytes
  - live source: `134` lines / `4264` bytes
  - main live drift:
    - the file still says the active bottleneck is rescue structure, not more negative-class narrowing
    - it is now slightly thicker around the first reformulation audit and live execution-note retention
    - the required branch-shape shift away from thermal/time/controller narration still holds

## 5) Grouped Read
- colder-witness order and late-alias gate:
  - `A1_ENTROPY_BRIDGE_COLDER_WITNESS_PACK__v1.md`
- helper-lift composition rule:
  - `A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__v1.md`
- rescue-shape reformulation rule:
  - `A1_ENTROPY_BRIDGE_REFORMULATION_PACK__v1.md`

## 6) Current Best Read
- the earlier active entropy-control batch remains historically useful, but it is not current on this three-file bridge-support trio
- live drift is bounded:
  - the executable branch and branch-budget spine remains unchanged
  - helper-decomposition control remains unchanged
  - cluster rescue topology remains unchanged
- the live trio still preserves the same high-level control picture:
  - executable honesty remains with the narrower correlation-side lane
  - colder-witness and helper-lift packs remain proposal-side steering and admissibility-shaping devices
  - reformulation remains a rescue-structure pivot rather than a fresh ontology declaration

## 7) Notes
- no active source was mutated
- no older batch was rewritten
- this packet is a bounded refresh surface, not a retroactive normalization of the earlier active `a1_state` entropy-control family
