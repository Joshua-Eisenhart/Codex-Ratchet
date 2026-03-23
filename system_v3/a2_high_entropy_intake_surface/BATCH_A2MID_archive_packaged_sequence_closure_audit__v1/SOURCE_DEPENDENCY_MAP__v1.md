# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_archive_packaged_sequence_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batches
- `BATCH_A2MID_archive_batch08_structural_memory_lock_transport_fences__v1`
- `BATCH_A2MID_archive_batch09_sim_protocol_evidence_hygiene_fences__v1`
- `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1`
- reused parent artifacts:
  - `SOURCE_DEPENDENCY_MAP__v1.md`
  - `SELECTION_RATIONALE__v1.md`
  - `A2_2_REFINED_CANDIDATES__v1.md`
  - `CONTRADICTION_PRESERVATION__v1.md`
  - `DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
  - `MANIFEST.json`

## Parent-batch read
- the archive-root packaged batch sequence is now complete through batch10
- the late archive segment from batch04 through batch10 is direct-child closed
- no additional folder-order package remains in the archive packaged lane

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
- `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`
- `BATCH_archive_surface_batch02_axes_apple_notes_igt_mapping__v1`
- `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1`
- `BATCH_A2MID_apple_axis_term_conflicts__v1`
- `BATCH_A2MID_holodeck_memory_worldmodel__v1`
- `BATCH_A2MID_grok_unified_admission_conflicts__v1`
- `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
- `BATCH_A2MID_reentry_gap_selection_audit__v1`

## Candidate dependency map
- `RC1_ARCHIVE_PACKAGED_SEQUENCE_IS_NOW_FOLDER_ORDER_CLOSED`
  - parent dependencies:
    - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC2_LATE_ARCHIVE_SEGMENT_BATCH04_TO_BATCH10_IS_DIRECT_CHILD_CLOSED`
  - parent dependencies:
    - `BATCH_A2MID_archive_batch08_structural_memory_lock_transport_fences__v1:MANIFEST.json`
    - `BATCH_A2MID_archive_batch09_sim_protocol_evidence_hygiene_fences__v1:MANIFEST.json`
    - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1:MANIFEST.json`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC3_REMAINING_UNCHILDED_ARCHIVE_PARENTS_ARE_BATCH01_BATCH02_BATCH03_ONLY`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_batch02_axes_apple_notes_igt_mapping__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC4_BATCH01_IS_LOWER_PRIORITY_BECAUSE_DIRECT_SOURCE_REFINEDFUEL_COVERAGE_IS_ALREADY_CLOSED`
  - comparison anchor dependencies:
    - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1:SOURCE_MAP__v1.md`
    - `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
- `RC5_BATCH03_IS_THE_NEXT_REAL_UNRESOLVED_ARCHIVE_PARENT`
  - comparison anchor dependencies:
    - `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
    - `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1:TENSION_MAP__v1.md`
    - `BATCH_A2MID_holodeck_memory_worldmodel__v1:A2_2_REFINED_CANDIDATES__v1.md`
    - `BATCH_A2MID_grok_unified_admission_conflicts__v1`
    - `BATCH_a2feed_holodeck_docs_source_map__v1:A2_3_DISTILLATES__v1.md`
    - `BATCH_a2feed_grok_unified_physics_source_map__v1:A2_3_DISTILLATES__v1.md`
- `RC6_LEDGER_STATE_OVERRIDES_STALE_FOLDER_ORDER_ASSUMPTION`
  - comparison anchor dependencies:
    - `BATCH_A2MID_reentry_gap_selection_audit__v1:SOURCE_DEPENDENCY_MAP__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`

## Quarantine dependency map
- `Q1_SEARCHING_FOR_ANOTHER_FOLDER_ORDER_ARCHIVE_PACKAGE`
  - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
- `Q2_REOPENING_BATCH04_TO_BATCH10_BY_DEFAULT`
  - `BATCH_A2MID_archive_batch08_structural_memory_lock_transport_fences__v1:MANIFEST.json`
  - `BATCH_A2MID_archive_batch09_sim_protocol_evidence_hygiene_fences__v1:MANIFEST.json`
  - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1:MANIFEST.json`
- `Q3_TREATING_BATCH10_TERMINAL_CLOSURE_AS_GLOBAL_ARCHIVE_COMPLETION`
  - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1:A2_2_REFINED_CANDIDATES__v1.md`
  - `BATCH_INDEX__v1.md`
- `Q4_EARLIEST_ARCHIVE_PARENT_AS_AUTOMATIC_NEXT_TARGET`
  - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1:SOURCE_MAP__v1.md`
  - `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1:A2_2_CANDIDATE_SUMMARIES__v1.md`
- `Q5_CLOSURE_AUDIT_AS_ACTIVE_A2_CONTROL_UPDATE`
  - `A2_MID_REFINEMENT_PROCESS__v1.md`
  - `BATCH_INDEX__v1.md`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the needed work here was lane-state audit and next-parent selection, not source recovery
  - the completed late-lane children, the remaining archive parent summaries, and the existing direct-source sibling reductions were sufficient to determine the next bounded target
