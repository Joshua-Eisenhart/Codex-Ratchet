# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a1state_entropy_support_pack_drift_refresh__v1`
Extraction mode: `ACTIVE_A1STATE_ENTROPY_SUPPORT_PACK_DRIFT_REFRESH_PASS`
Date: 2026-03-09

## 1) Scope
- bounded live-source refresh over the drifted support/control subset inside the earlier active `a1_state` entropy-support family
- purpose:
  - preserve the exact four live support/control files that no longer match the earlier first-pass manifest
  - keep the earlier family batch intact as a historical snapshot
  - record where alias-lift, helper-leak stripping, structure-decomposition control, and thermal/time rescue follow-up changed after the original pass

## 2) Source Set
- live drifted source members:
  - `system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
  - `system_v3/a1_state/A1_ENTROPY_HELPER_LEAK_STRIP_PACK__v1.md`
  - `system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md`
  - `system_v3/a1_state/A1_ENTROPY_THERMAL_TIME_RESCUE_PACK__v1.md`
- unchanged members still preserved by the earlier family batch:
  - `A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md`
  - `A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md`
  - `A1_ENTROPY_FAMILY_MERGE_FENCE__v1.md`
  - `A1_ENTROPY_PROBE_COMPANION_PACK__v1.md`
  - `A1_ENTROPY_RATE_LIFT_PACK__v1.md`
  - `A1_ENTROPY_REQUIRED_PROBE_WITNESS_PACK__v1.md`
  - `A1_ENTROPY_RESCUE_TARGET_DECOMPOSITION_PACK__v1.md`
- comparison anchors:
  - `BATCH_systemv3_active_a1state_entropy_support_pack_family__v1/MANIFEST.json`
  - `BATCH_systemv3_active_a1state_campaign_graveyard_validity_packet__v1/MANIFEST.json`

## 3) Why This Refresh Exists
- the queued reuse check failed because the earlier active entropy-support family manifest no longer matched live repo state
- drift count:
  - changed members: `4`
  - unchanged members from the earlier family: `7`
- this packet does not replace the earlier batch
- it preserves the earlier batch as a source-bound March 9 snapshot and adds the now-live support/control delta surface beside it

## 4) Drifted Membership By Function
- `a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
  - old snapshot: `163` lines / `5317` bytes
  - live source: `163` lines / `5279` bytes
  - main live drift:
    - the file still treats `pairwise_correlation_spread_functional` as a colder executable alias candidate rather than a landed head
    - the alias audit and admissibility block remain, but the live surface is slightly tighter
    - the same role map still holds: `correlation_polarity` head-ready, diversity passenger-only, alias witness-only
- `a1_state/A1_ENTROPY_HELPER_LEAK_STRIP_PACK__v1.md`
  - old snapshot: `179` lines / `5728` bytes
  - live source: `177` lines / `5370` bytes
  - main live drift:
    - the file still names helper fragmentation as the next blocker after executable rescue
    - lone-helper bans and attached-bridge requirements still hold
    - the live surface is shorter, not a doctrine reversal
- `a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md`
  - old snapshot: `125` lines / `4791` bytes
  - live source: `124` lines / `4441` bytes
  - main live drift:
    - the file still says local structure is blocked by lower-loop compound decomposition, not proposal drift
    - direct structure targets remain proposal-side while executable work stays helper-only
    - the live surface is slightly tighter while preserving the same bottleneck read
- `a1_state/A1_ENTROPY_THERMAL_TIME_RESCUE_PACK__v1.md`
  - old snapshot: `116` lines / `4463` bytes
  - live source: `115` lines / `4178` bytes
  - main live drift:
    - the focused thermal/time split and its bounded negative frontier remain intact
    - the live audit still says the narrowed frontier executes but does not move the basin
    - the same next-step pressure toward rescue-structure change still holds

## 5) Grouped Read
- alias and structure-side landing pressure:
  - `A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
  - `A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md`
- helper leakage and attached-bridge enforcement:
  - `A1_ENTROPY_HELPER_LEAK_STRIP_PACK__v1.md`
- narrowed thermal/time rescue pressure:
  - `A1_ENTROPY_THERMAL_TIME_RESCUE_PACK__v1.md`

## 6) Current Best Read
- the earlier active entropy-support batch remains historically useful, but it is not current on this four-file support/control quartet
- live drift is bounded:
  - executable entrypoint logic remains unchanged
  - diversity-structure lift remains unchanged
  - family-merge fence remains unchanged
  - probe witness support, rate lift, and rescue-target decomposition remain unchanged
- the live quartet still preserves the same support-layer picture:
  - alias and diversity still matter without becoming head-ready
  - helper leakage is still a real failure class, but aggressive suppression is not a clean fix
  - local structure remains blocked by lower-loop decomposition
  - thermal/time rescue narrowing remains operational but insufficient by itself

## 7) Notes
- no active source was mutated
- no older batch was rewritten
- this packet is a bounded refresh surface, not a retroactive normalization of the earlier active `a1_state` entropy-support family
