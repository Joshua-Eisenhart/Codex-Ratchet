# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_packaged_sequence_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `ARCHIVE_PACKAGED_SEQUENCE_IS_NOW_FOLDER_ORDER_CLOSED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the archive packaged batch campaign is now folder-order closed:
  - batch01 through batch10 all exist as first-pass intake batches
  - no additional archive-root package remains in folder order

Why this survives reduction:
- it preserves the routing fact that another folder-order package does not exist
- it blocks stale queue behavior

Source lineage:
- parent consequence:
  - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim the archive lane is globally complete
- it preserves only the folder-order closure fact

## Candidate RC2) `LATE_ARCHIVE_SEGMENT_BATCH04_TO_BATCH10_IS_DIRECT_CHILD_CLOSED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current archive late segment is direct-child closed:
  - batch04
  - batch05
  - batch06
  - batch07
  - batch08
  - batch09
  - batch10

Why this survives reduction:
- it preserves the strongest closure boundary inside the archive lane
- it blocks reopening already-childed late archive parents by default

Source lineage:
- child manifests:
  - `BATCH_A2MID_archive_leviathan_hybrid_authority_drift__v1`
  - `BATCH_A2MID_archive_batch05_mint_boundary_fences__v1`
  - `BATCH_A2MID_archive_batch06_upgrade_control_fences__v1`
  - `BATCH_A2MID_archive_batch07_audit_gap_zip_taxonomy_fences__v1`
  - `BATCH_A2MID_archive_batch08_structural_memory_lock_transport_fences__v1`
  - `BATCH_A2MID_archive_batch09_sim_protocol_evidence_hygiene_fences__v1`
  - `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not deny residual value in the archive lane
- it preserves only the rule that late-segment parents are no longer the strongest unresolved targets

## Candidate RC3) `REMAINING_UNCHILDED_ARCHIVE_PARENTS_ARE_BATCH01_BATCH02_BATCH03_ONLY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- after late-lane closure, the remaining early archive parents without A2-mid children are:
  - batch01
  - batch02
  - batch03

Why this survives reduction:
- it reduces the remaining archive gap set cleanly
- it prevents diffuse re-entry drift across already-closed parents

Source lineage:
- archive parent summaries:
  - `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`
  - `BATCH_archive_surface_batch02_axes_apple_notes_igt_mapping__v1`
  - `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rank those three equally
- it preserves only the narrowed residual set

## Candidate RC4) `BATCH01_IS_LOWER_PRIORITY_BECAUSE_DIRECT_SOURCE_REFINEDFUEL_COVERAGE_IS_ALREADY_CLOSED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- batch01 is not the next best target because:
  - its underlying refined-fuel nonsims root is already direct-source closed
  - its main constraint-ladder family has extensive stronger sibling coverage
  - the archive carrier itself is therefore lower marginal value than the still-mixed archive parents

Why this survives reduction:
- it preserves a real routing distinction between direct-source closure and archive-package closure
- it blocks naive earliest-parent selection

Source lineage:
- comparison anchor:
  - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
- archive parent summary:
  - `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`

Preserved limits:
- this batch does not say batch01 has no value
- it preserves only the rule that batch01 is not the strongest next target now

## Candidate RC5) `BATCH03_IS_THE_NEXT_REAL_UNRESOLVED_ARCHIVE_PARENT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest next archive re-entry target is batch03 because:
  - it remains unchilded
  - it is still a mixed archive parent
  - both major source-side strands already have usable sibling reductions:
    - holodeck memory/world-model
    - grok unified admission conflicts

Why this survives reduction:
- it gives the archive lane a real next target after sequence closure
- it uses existing sibling reductions to constrain a mixed archive parent without reopening raw corpus blindly

Source lineage:
- archive parent:
  - `BATCH_archive_surface_batch03_physics_grok_holodeck_cluster__v1`
- comparison anchors:
  - `BATCH_A2MID_holodeck_memory_worldmodel__v1`
  - `BATCH_A2MID_grok_unified_admission_conflicts__v1`
  - `BATCH_a2feed_holodeck_docs_source_map__v1`
  - `BATCH_a2feed_grok_unified_physics_source_map__v1`

Preserved limits:
- this batch does not claim batch03 is the final most important archive parent in all respects
- it preserves only the rule that batch03 is the strongest next bounded re-entry target now

## Candidate RC6) `LEDGER_STATE_OVERRIDES_STALE_FOLDER_ORDER_ASSUMPTION`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- selection must follow:
  - current ledger state
  - current child coverage
  - current residual set
- not stale queue text or imagined remaining folder-order packages

Why this survives reduction:
- it is the main process rule required to keep the lane bounded
- it matches the earlier re-entry gap audit precedent

Source lineage:
- comparison anchor:
  - `BATCH_A2MID_reentry_gap_selection_audit__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rewrite selection globally
- it preserves only the routing rule for this closure state

## Quarantined Residue Q1) `SEARCHING_FOR_ANOTHER_FOLDER_ORDER_ARCHIVE_PACKAGE`
Status:
- `QUARANTINED`

Preserved residue:
- acting as if another archive-root packaged batch still exists in folder order

Why it stays quarantined:
- the sequence is exhausted at batch10

Source lineage:
- `BATCH_A2MID_archive_batch10_terminal_savekit_vocabulary_fences__v1`

## Quarantined Residue Q2) `REOPENING_BATCH04_TO_BATCH10_BY_DEFAULT`
Status:
- `QUARANTINED`

Preserved residue:
- reopening already-childed late archive parents as if they were still the main unresolved gap

Why it stays quarantined:
- the late archive segment is now direct-child closed

Source lineage:
- late archive child manifests
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q3) `TREATING_BATCH10_TERMINAL_CLOSURE_AS_GLOBAL_ARCHIVE_COMPLETION`
Status:
- `QUARANTINED`

Preserved residue:
- treating terminal package closure as if no archive re-entry target remained anywhere

Why it stays quarantined:
- batch01, batch02, and batch03 still remain unchilded archive parents

Source lineage:
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q4) `EARLIEST_ARCHIVE_PARENT_AS_AUTOMATIC_NEXT_TARGET`
Status:
- `QUARANTINED`

Preserved residue:
- choosing batch01 just because it is earliest in order

Why it stays quarantined:
- direct-source refined-fuel coverage is already closed enough that batch01 is lower-yield than batch03 right now

Source lineage:
- `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
- `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`

## Quarantined Residue Q5) `CLOSURE_AUDIT_AS_ACTIVE_A2_CONTROL_UPDATE`
Status:
- `QUARANTINED`

Preserved residue:
- treating this routing audit as if it were an active A2 control-memory update

Why it stays quarantined:
- the A2-mid process allows bounded routing and reduction only, not direct control-memory promotion

Source lineage:
- `A2_MID_REFINEMENT_PROCESS__v1`
