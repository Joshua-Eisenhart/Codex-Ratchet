# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_post_archive_a2feed_bigdoc_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `ARCHIVE_ROOT_PACKAGED_BATCH01_TO_BATCH10_IS_NOW_DIRECT_CHILD_CLOSED_ENOUGH_TO_EXIT_AS_PRIMARY_REENTRY_LANE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the archive-root packaged family is no longer the strongest immediate re-entry lane because:
  - the archive packaged-sequence closure audit already exists
  - the early remaining archive parents now also have children
  - reopening that lane would now mostly repeat closure work rather than expose the best unresolved source-bearing parent

Why this survives reduction:
- it preserves the main routing fact needed before leaving the archive lane
- it blocks stale queue reuse

Source lineage:
- archive-lane closure anchor:
  - `BATCH_A2MID_archive_packaged_sequence_closure_audit__v1`
- completed early children:
  - `BATCH_A2MID_archive_batch01_foundation_overlay_contradiction_fences__v1`
  - `BATCH_A2MID_archive_batch02_mapping_lock_projection_fences__v1`
  - `BATCH_A2MID_archive_batch03_holodeck_grok_split_fences__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim archive work is globally complete
- it preserves only that the archive-root packaged family is no longer the main next-target lane

## Candidate RC2) `EARLY_A2FEED_BIGDOC_SET_IS_NOW_THE_PRIMARY_SOURCE_BEARING_UNCHILDED_REENTRY_POOL`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest remaining source-bearing unresolved parent pool is now:
  - `BATCH_a2feed_a0_threadsave_source_map__v1`
  - `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`
  - `BATCH_a2feed_grok_eisenhart_model_source_map__v1`
  - `BATCH_a2feed_grok_gemini_digested_model_source_map__v1`

Why this survives reduction:
- it gives the next selection step a real bounded pool
- it prevents drift back into already-childed archive packages or low-yield inventory revisits

Source lineage:
- comparison anchors:
  - the four source maps above
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rank the whole pool equally
- it preserves only the narrowed unresolved set

## Candidate RC3) `A0_THREADSAVE_REMAINS_REAL_BUT_INVENTORY_FIRST_AND_LOWER_YIELD_THAN_BIGDOC_REENTRY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the A0 threadsave root remains valuable for lineage across:
  - bootpacks
  - reports
  - snapshots
  - export cycles
  - sim-runner protocol residue
- but it is still inventory-first and composite enough that it should not outrank a cleaner high-yield revisit_required big-doc next

Why this survives reduction:
- it preserves a real priority demotion without erasing the source
- it blocks naive earliest-file or first-root bias

Source lineage:
- `BATCH_a2feed_a0_threadsave_source_map__v1`

Preserved limits:
- this batch does not say the A0 threadsave root is unimportant
- it preserves only that it is not the strongest immediate next target

## Candidate RC4) `GPT_THREAD_A1_TRIGRAM_HAS_THE_CLEANEST_BOUNDED_SUBPASS_SEAMS_IN_THE_CURRENT_POOL`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the GPT trigram source map already names the right narrower future passes:
  - Thread A / Thread B bridge law
  - SIM and evidence protocol material
  - correlation-first foundation material
  - axis and trigram conflict material

Why this survives reduction:
- it is the clearest boundedness signal in the current pool
- it makes the next reduction step legible before reopening raw source

Source lineage:
- `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`

Preserved limits:
- this batch does not yet choose which of those sub-passes will dominate the child reduction
- it preserves only that the parent is cleanly segmentable

## Candidate RC5) `GPT_THREAD_A1_TRIGRAM_IS_THE_NEXT_REAL_UNRESOLVED_REENTRY_TARGET`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the next real unresolved re-entry target is:
  - `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`
- because it combines:
  - `REVISIT_REQUIRED` status
  - explicit internal sub-pass seams
  - strong nearby sibling anchors

Why this survives reduction:
- it gives the lane a concrete next move after archive closure
- it uses already-earned sibling reductions to bound a very large mixed transcript

Source lineage:
- source-bearing parent:
  - `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`
- comparison anchors:
  - `BATCH_A2MID_branchthread_workflow_repair__v1`
  - `BATCH_A2MID_apple_axis_term_conflicts__v1`
  - `BATCH_A2MID_bootpack_thread_a_outer_interface__v1`

Preserved limits:
- this batch does not claim the GPT trigram file is canon or low-noise
- it preserves only that it is the best next bounded re-entry target now

## Candidate RC6) `SOURCE_BEARING_REVISIT_REQUIRED_BIGDOC_REENTRY_BEATS_CACHE_DEEP_ARCHIVE_AND_BROAD_MODEL_REVISITS_NOW`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- current priority should favor the GPT trigram big-doc over:
  - purgeable cache export families
  - deep-archive topology and inventory families
  - broader integrated-model revisits with heavier duplication or worldview load

Why this survives reduction:
- it preserves the priority rule that source-bearing bounded re-entry should outrank lower-yield inventory families and broader noisier revisits
- it keeps the lane focused on the strongest next source-bearing parent

Source lineage:
- comparison anchors:
  - `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
  - `BATCH_archive_surface_deep_archive_root_milestone_split__v1`
  - `BATCH_a2feed_grok_eisenhart_model_source_map__v1`
  - `BATCH_a2feed_grok_gemini_digested_model_source_map__v1`
  - `BATCH_A2MID_reentry_gap_selection_audit__v1`

Preserved limits:
- this batch does not deny later value in those deferred families
- it preserves only the current ordering rule

## Quarantined Residue Q1) `REOPENING_ARCHIVE_ROOT_PACKAGED_BATCH01_TO_BATCH10_AS_IF_IT_WERE_STILL_THE_MAIN_UNRESOLVED_LANE`
Status:
- `QUARANTINED`

Preserved residue:
- acting as if archive-root packaged closure work still needs to be repeated before moving on

Why it stays quarantined:
- the archive family already has the needed closure and child reductions for routing purposes

Source lineage:
- `BATCH_A2MID_archive_packaged_sequence_closure_audit__v1`
- `BATCH_A2MID_archive_batch01_foundation_overlay_contradiction_fences__v1`
- `BATCH_A2MID_archive_batch02_mapping_lock_projection_fences__v1`
- `BATCH_A2MID_archive_batch03_holodeck_grok_split_fences__v1`

## Quarantined Residue Q2) `TREATING_ARCHIVE_PACKAGE_CLOSURE_AS_GLOBAL_LEDGER_COMPLETION`
Status:
- `QUARANTINED`

Preserved residue:
- reading archive-lane closure as if no further unresolved source-bearing parent remained anywhere in the intake surface

Why it stays quarantined:
- the early a2feed big-doc pool remains unchilded

Source lineage:
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q3) `DEFAULTING_NEXT_TO_PURGEABLE_CACHE_OR_DEEP_ARCHIVE_INVENTORY_FAMILIES`
Status:
- `QUARANTINED`

Preserved residue:
- choosing lower-yield archive inventory revisits simply because they remain unresolved

Why it stays quarantined:
- source-bearing big-doc re-entry is stronger now

Source lineage:
- `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
- `BATCH_archive_surface_deep_archive_root_milestone_split__v1`

## Quarantined Residue Q4) `DEFAULTING_NEXT_TO_ALREADY_CHILD_CLOSED_OR_ALREADY_RESOLVED_NEARBY_PARENTS`
Status:
- `QUARANTINED`

Preserved residue:
- treating branchthread, apple-axis, or archive packaged parents as if they were still default next targets

Why it stays quarantined:
- their role is now comparison-anchor support rather than primary unresolved parent selection

Source lineage:
- `BATCH_A2MID_branchthread_workflow_repair__v1`
- `BATCH_A2MID_apple_axis_term_conflicts__v1`
- `BATCH_A2MID_archive_packaged_sequence_closure_audit__v1`

## Quarantined Residue Q5) `TREATING_A0_THREADSAVE_INVENTORY_SEED_AS_HIGHER_PRIORITY_THAN_THE_GPT_TRIGRAM_BIGDOC`
Status:
- `QUARANTINED`

Preserved residue:
- preferring the A0 threadsave root simply because it is earlier and broad

Why it stays quarantined:
- its composite inventory role is lower-yield than the GPT trigram file's cleaner bounded seams

Source lineage:
- `BATCH_a2feed_a0_threadsave_source_map__v1`
- `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`

## Quarantined Residue Q6) `SELECTION_AUDIT_AS_ACTIVE_A2_CONTROL_UPDATE`
Status:
- `QUARANTINED`

Preserved residue:
- treating this routing packet as if it directly mutated active control memory

Why it stays quarantined:
- this batch is A2-mid selection only

Source lineage:
- `A2_MID_REFINEMENT_PROCESS__v1.md`
- `BATCH_INDEX__v1.md`
