# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_early_a2feed_bigdoc_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `EARLY_A2FEED_BIGDOC_LANE_IS_NOW_DIRECT_CHILD_CLOSED_ENOUGH_TO_EXIT_AS_PRIMARY_REENTRY_POOL`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the early `a2_feed` big-doc lane is now direct-child closed enough to stop being the strongest immediate re-entry pool

Why this survives reduction:
- the four main parents in that lane now each have bounded A2-mid children
- this blocks stale repetition of an already-completed lane

Source lineage:
- child manifests:
  - `BATCH_A2MID_a0_threadsave_operating_pattern_fences__v1`
  - `BATCH_A2MID_gpt_thread_a1_bridge_evidence_trigram_split__v1`
  - `BATCH_A2MID_grok_eisenhart_swap_validation_fences__v1`
  - `BATCH_A2MID_grok_gemini_registry_manifesto_axis_fences__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim the whole intake surface is closed
- it preserves only that this specific lane can now be exited

## Candidate RC2) `POST_ARCHIVE_A2FEED_BIGDOC_SELECTION_AUDIT_IS_NOW_DISCHARGED_BY_CHILD_COMPLETION`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the earlier audit that nominated the early a2feed big-doc lane has now been fully discharged by actual child completion

Why this survives reduction:
- it prevents stale queue text from continuing to drive lane choice
- it records that the earlier routing decision has already been executed

Source lineage:
- comparison anchor:
  - `BATCH_A2MID_post_archive_a2feed_bigdoc_selection_audit__v1`

Preserved limits:
- this batch does not erase the value of the earlier audit
- it preserves only that its chosen lane is now complete enough to leave

## Candidate RC3) `NEXT_UNRESOLVED_SOURCE_BEARING_POOL_NOW_SITS_IN_ARCHIVE_SAVE_EXPORT_AND_DEEP_ARCHIVE_LANES`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest unresolved source-bearing archive pool now sits in:
  - the purgeable cache save-export family
  - the deep-archive milestone root family

Why this survives reduction:
- it gives the next selection step a real bounded pool
- it prevents drift back into already-childed early a2feed parents

Source lineage:
- comparison anchors:
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rank the whole unresolved archive space equally
- it preserves only the narrowed top-level pool

## Candidate RC4) `PURGEABLE_CACHE_SAVE_EXPORT_FAMILY_IS_THE_STRONGEST_NEXT_REENTRY_TARGET`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest next re-entry target is:
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`

Why this survives reduction:
- it is bounded and checksum-tight
- it preserves the clearest export-lineage and retention-gradient seam
- it directly witnesses fuller save bodies than later archive-derived extraction packages

Source lineage:
- comparison anchor:
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`

Preserved limits:
- this batch does not claim the cache family is canon or replay-ready
- it preserves only that it is the best next bounded target now

## Candidate RC5) `DEEP_ARCHIVE_ROOT_MILESTONE_SPLIT_REMAINS_REAL_BUT_LOWER_YIELD_THAN_CACHE_EXPORT_REENTRY_NOW`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the deep-archive root remains a real later target, but it is lower-yield now than the cache export family because it is still mainly a topology and registry root over a very large corpus

Why this survives reduction:
- it preserves a real demotion rule without erasing the root family
- it blocks folder-order bias from outranking boundedness

Source lineage:
- comparison anchor:
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`

Preserved limits:
- this batch does not say the deep-archive root has no value
- it preserves only that it should not outrank the cache export bridge now

## Candidate RC6) `CACHE_EXPORT_REENTRY_SHOULD_PRECEDE_DEEP_ARCHIVE_DESCENT_AND_DESCENDANT_RUN_SELECTION`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the cleaner cache export bridge should be reduced before:
  - deep-archive root descent
  - migrated-run-root descent
  - descendant run-family selection

Why this survives reduction:
- it preserves a cleaner lane ordering rule after early a2feed closure
- it keeps the next step bounded and comparable

Source lineage:
- cache anchor:
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- deep-archive anchor:
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C5`

Preserved limits:
- this batch does not permanently freeze later deep-archive ordering
- it preserves only the best current next step

## Quarantined Residue Q1) `REOPENING_EARLY_A2FEED_BIGDOC_LANE_AS_IF_IT_WERE_STILL_UNCHILDED`
Status:
- `QUARANTINED`

Preserved residue:
- acting as if the early a2feed big-doc lane still lacked direct children

Why it stays quarantined:
- the lane now has direct bounded children across its four main parents

Source lineage:
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q2) `TREATING_EARLY_A2FEED_LANE_CLOSURE_AS_GLOBAL_LEDGER_COMPLETION`
Status:
- `QUARANTINED`

Preserved residue:
- reading this lane closure as if no real unresolved source-bearing archive parent remained

Why it stays quarantined:
- unresolved archive save-export and deep-archive families still remain

Source lineage:
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q3) `DEFAULTING_NEXT_TO_DEEP_ARCHIVE_ROOT_JUST_BECAUSE_FOLDER_ORDER_CONTINUES`
Status:
- `QUARANTINED`

Preserved residue:
- choosing the deep-archive root next simply because folder order continues there

Why it stays quarantined:
- the cache export family is more bounded and higher-yield now

Source lineage:
- `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`

## Quarantined Residue Q4) `SKIPPING_CACHE_EXPORT_BRIDGE_AND_JUMPING_STRAIGHT_TO_DEEP_ARCHIVE_DESCENDANT_RUNS`
Status:
- `QUARANTINED`

Preserved residue:
- jumping directly into descendant deep-archive run families before resolving the cleaner cache export bridge

Why it stays quarantined:
- the lane still benefits from a smaller export-lineage bridge first

Source lineage:
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
- `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C5`

## Quarantined Residue Q5) `TREATING_PURGEABLE_CACHE_AS_NONREUSABLE_ONLY_BECAUSE_IT_IS_MARKED_SAFE_TO_DELETE`
Status:
- `QUARANTINED`

Preserved residue:
- dismissing the cache family as nonreusable only because it is marked safe to delete

Why it stays quarantined:
- the family still preserves fuller save-export content and retention-gradient evidence

Source lineage:
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`

## Quarantined Residue Q6) `SELECTION_AUDIT_AS_ACTIVE_A2_CONTROL_UPDATE`
Status:
- `QUARANTINED`

Preserved residue:
- treating this routing audit as if it directly updated active control memory

Why it stays quarantined:
- it is only a bounded A2-mid routing packet

Source lineage:
- `A2_MID_REFINEMENT_PROCESS__v1.md`
