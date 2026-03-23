# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_early_a2feed_bigdoc_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batches
- `BATCH_A2MID_a0_threadsave_operating_pattern_fences__v1`
- `BATCH_A2MID_gpt_thread_a1_bridge_evidence_trigram_split__v1`
- `BATCH_A2MID_grok_eisenhart_swap_validation_fences__v1`
- `BATCH_A2MID_grok_gemini_registry_manifesto_axis_fences__v1`
- reused parent artifacts:
  - `MANIFEST.json`
  - `SOURCE_DEPENDENCY_MAP__v1.md`
  - `A2_2_REFINED_CANDIDATES__v1.md`
  - `CONTRADICTION_PRESERVATION__v1.md`
  - `DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`

## Parent-batch read
- the four strongest early a2feed big-doc parents are now direct-child closed
- the prior selection audit that nominated this lane has therefore been discharged
- the next unresolved source-bearing decision moves into archive save-export versus deep-archive routing

## Control-surface dependencies read but not mutated
- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
- `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/A2_MID_REFINEMENT_PROCESS__v1.md`
- `system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`

## Comparison anchors
- `BATCH_A2MID_post_archive_a2feed_bigdoc_selection_audit__v1`
- `BATCH_A2MID_archive_packaged_sequence_closure_audit__v1`
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
- `BATCH_archive_surface_deep_archive_root_milestone_split__v1`

## Candidate dependency map
- `RC1_EARLY_A2FEED_BIGDOC_LANE_IS_NOW_DIRECT_CHILD_CLOSED_ENOUGH_TO_EXIT_AS_PRIMARY_REENTRY_POOL`
  - parent dependencies:
    - `BATCH_A2MID_a0_threadsave_operating_pattern_fences__v1:MANIFEST.json`
    - `BATCH_A2MID_gpt_thread_a1_bridge_evidence_trigram_split__v1:MANIFEST.json`
    - `BATCH_A2MID_grok_eisenhart_swap_validation_fences__v1:MANIFEST.json`
    - `BATCH_A2MID_grok_gemini_registry_manifesto_axis_fences__v1:MANIFEST.json`
    - `BATCH_INDEX__v1.md`
- `RC2_POST_ARCHIVE_A2FEED_BIGDOC_SELECTION_AUDIT_IS_NOW_DISCHARGED_BY_CHILD_COMPLETION`
  - comparison anchor dependencies:
    - `BATCH_A2MID_post_archive_a2feed_bigdoc_selection_audit__v1:A2_2_REFINED_CANDIDATES__v1.md:RC2`
    - `BATCH_A2MID_post_archive_a2feed_bigdoc_selection_audit__v1:A2_2_REFINED_CANDIDATES__v1.md:RC5`
- `RC3_NEXT_UNRESOLVED_SOURCE_BEARING_POOL_NOW_SITS_IN_ARCHIVE_SAVE_EXPORT_AND_DEEP_ARCHIVE_LANES`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:MANIFEST.json`
    - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:MANIFEST.json`
    - `BATCH_INDEX__v1.md`
- `RC4_PURGEABLE_CACHE_SAVE_EXPORT_FAMILY_IS_THE_STRONGEST_NEXT_REENTRY_TARGET`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:MANIFEST.json`
- `RC5_DEEP_ARCHIVE_ROOT_MILESTONE_SPLIT_REMAINS_REAL_BUT_LOWER_YIELD_THAN_CACHE_EXPORT_REENTRY_NOW`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
    - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:MANIFEST.json`
- `RC6_CACHE_EXPORT_REENTRY_SHOULD_PRECEDE_DEEP_ARCHIVE_DESCENT_AND_DESCENDANT_RUN_SELECTION`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
    - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C2`
    - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C5`

## Quarantine dependency map
- `Q1_REOPENING_EARLY_A2FEED_BIGDOC_LANE_AS_IF_IT_WERE_STILL_UNCHILDED`
  - `BATCH_INDEX__v1.md`
- `Q2_TREATING_EARLY_A2FEED_LANE_CLOSURE_AS_GLOBAL_LEDGER_COMPLETION`
  - `BATCH_INDEX__v1.md`
- `Q3_DEFAULTING_NEXT_TO_DEEP_ARCHIVE_ROOT_JUST_BECAUSE_FOLDER_ORDER_CONTINUES`
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:MANIFEST.json`
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:MANIFEST.json`
- `Q4_SKIPPING_CACHE_EXPORT_BRIDGE_AND_JUMPING_STRAIGHT_TO_DEEP_ARCHIVE_DESCENDANT_RUNS`
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
- `Q5_TREATING_PURGEABLE_CACHE_AS_NONREUSABLE_ONLY_BECAUSE_IT_IS_MARKED_SAFE_TO_DELETE`
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C1`
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1:A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q6_SELECTION_AUDIT_AS_ACTIVE_A2_CONTROL_UPDATE`
  - `A2_MID_REFINEMENT_PROCESS__v1.md`
  - `BATCH_INDEX__v1.md`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - this batch is a routing audit
  - the live ledger and first-pass cache and deep-archive parent summaries were sufficient to pick the next target without reopening raw archive files
