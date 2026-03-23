# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION NOTE
Batch: `BATCH_A2MID_reentry_gap_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this audit batch was selected
- the queued next step was no longer another source reduction but a closure-aware audit over the current A2-mid re-entry lane
- the two most recent refined-fuel re-entry children now give enough evidence to test whether that local lane is actually closed or whether stale queue text is still pointing back at already-covered parents
- the ledger already contains the stronger answer, so the bounded job here is to record that answer as an explicit selection packet

## Why this audit is bounded
- it does not attempt a new raw-source reread
- it does not reopen the paired `Constraints` parents
- it does not try to reduce every unresolved parent in the whole intake surface
- it keeps only the smaller reusable packets:
  - direct-child closure for the current refined-fuel pair
  - ledger-first target selection
  - the rule that the a2feed Thread B bootpack parent remains unresolved
  - the rule that the existing upgrade-doc Thread B child is additive rather than duplicate coverage
  - compact-engine-pattern priority over giant source-map revisits

## Why comparison anchors were used
- `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
  - used as the nearest closure-audit precedent for ending coverage work by selecting the next real unresolved target
- `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1`
  - used as the strongest compact unresolved parent candidate once the current refined-fuel re-entry pair was shown to be child-closed
- `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1`
  - used to test whether existing Thread B child coverage already closes the a2feed parent or only provides sibling context from a different source family

## Why no raw reread was needed
- the paired `Constraints` children already proved the local refined-fuel pair was closed at the direct-child level
- the ledger already exposes which unresolved parents still lack children
- the a2feed Thread B parent already has enough source-map and distillate structure to justify next-step selection without reopening raw source during this audit packet

## Deferred alternatives
- `BATCH_a2feed_leviathan_family_source_map__v1`
  - deferred because it remains a much larger source-map revisit with lower bounded next-step yield than the compact unresolved Thread B engine-pattern parent
- `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`
  - deferred because it is also a giant mixed source-map revisit rather than a narrow engine-pattern seam
- `BATCH_upgrade_docs_megaboot_ratchet_suite_source_map__v1`
  - deferred because it is broad and composite, while the unresolved Thread B parent is smaller and more immediately reducible
- `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`
  - deferred because it is output-heavy archival packaging rather than a cleaner compact live-source parent

## Best next existing intake target
- `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1`
