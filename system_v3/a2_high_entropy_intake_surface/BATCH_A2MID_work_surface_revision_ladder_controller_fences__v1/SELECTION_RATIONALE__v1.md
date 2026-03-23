# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_work_surface_revision_ladder_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why This Parent
- `BATCH_work_surface_delta_update_bootstrap_revision_ladder__v1` is the next uncovered parent after the first active A1 judgment reduction
- the parent is tightly bounded around one spillover revision arc:
  - delta `v2` to `v4`
  - update-pack `v2`
  - bootstrap `v3` to `v4__rev1`
- it already preserves concrete drift signatures, so a second-pass reduction can stay narrow without rereading raw source families

## Why This Reduction Goal
- bounded goal:
  - isolate only the controller-usable revision-ladder rules for:
    - delta-core stability with extract accretion
    - lean-patch intent versus scale settlement failure
    - update-pack stale metadata and forward-reference drift
    - bootstrap self-label mismatch
    - bootstrap read-first control-spine tightening
    - thin and uneven sidecar integrity
- excluded for now:
  - later bootstrap revisions after `v4__rev1`
  - any claim of downstream application success
  - promotion of any `work/out` artifact into active transport or runtime law

## Deferred Alternatives
- `BATCH_systemv3_active_a1state_entropy_control_pack_family__v1`
  - strongest adjacent active sibling because it continues the `a1_state` family in folder order
- `BATCH_work_surface_bootstrap_revision_ladder_completion__v1`
  - strongest work-surface follow-on once the first revision ladder is narrowed
- `BATCH_systemv3_active_a1state_entropy_support_pack_family__v1`
  - later active sibling after the first entropy-control family is handled
