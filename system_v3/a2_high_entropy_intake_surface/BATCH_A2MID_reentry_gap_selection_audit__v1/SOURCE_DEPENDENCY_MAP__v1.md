# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID DEPENDENCY MAP
Batch: `BATCH_A2MID_reentry_gap_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Parent batches
- `BATCH_A2MID_constraints_entropy_chain_fences__v1`
- `BATCH_A2MID_constraints_foundation_governance_fences__v1`
- reused parent artifacts:
  - `SOURCE_DEPENDENCY_MAP__v1.md`
  - `SELECTION_RATIONALE__v1.md`
  - `A2_2_REFINED_CANDIDATES__v1.md`
  - `CONTRADICTION_PRESERVATION__v1.md`
  - `DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
  - `MANIFEST.json`

## Parent-batch read
- the current refined-fuel re-entry pair is now closed at the direct child level
- both paired `Constraints` siblings already have their stronger direct term-conflict parents reduced into narrower A2-mid children
- no additional bounded value remains in immediately reopening those same paired parents before auditing the broader unresolved queue

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
- `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
  - used as the nearest repo-local precedent for a closure-aware audit that ends by selecting the next real unresolved target instead of pretending source coverage itself is still the main gap
- `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1`
  - used as the strongest current compact unresolved parent candidate after the refined-fuel re-entry pair closed
- `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1`
  - used to test whether the existing upgrade-doc Thread B child already covers the a2feed Thread B parent or only provides additive sibling context

## Candidate dependency map
- `RC1 CURRENT_REENTRY_PAIR_IS_DIRECT_CHILD_CLOSED`
  - parent dependencies:
    - `BATCH_A2MID_constraints_entropy_chain_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
    - `BATCH_A2MID_constraints_foundation_governance_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
    - `BATCH_A2MID_constraints_entropy_chain_fences__v1:MANIFEST.json`
    - `BATCH_A2MID_constraints_foundation_governance_fences__v1:MANIFEST.json`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC2 LEDGER_STATE_OVERRIDES_STALE_QUEUE_TEXT`
  - parent dependencies:
    - `BATCH_A2MID_constraints_entropy_chain_fences__v1:SELECTION_RATIONALE__v1.md`
    - `BATCH_A2MID_constraints_foundation_governance_fences__v1:SELECTION_RATIONALE__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC3 NEXT_REAL_UNRESOLVED_PARENT_IS_A2FEED_THREAD_B_BOOTPACK_KERNEL`
  - comparison anchor dependencies:
    - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:SOURCE_MAP__v1.md`
    - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:A2_3_DISTILLATES__v1.md`
    - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:MANIFEST.json`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`
- `RC4 UPGRADE_DOC_THREAD_B_CHILD_IS_ADDITIVE_NOT_DUPLICATIVE`
  - comparison anchor dependencies:
    - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:SOURCE_DEPENDENCY_MAP__v1.md`
    - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:A2_2_REFINED_CANDIDATES__v1.md`
    - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:A2_3_DISTILLATES__v1.md`
- `RC5 COMPACT_ENGINE_PATTERN_REENTRY_BEATS_GIANT_SOURCE_MAP_REVISITS`
  - comparison anchor dependencies:
    - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1:SOURCE_MAP__v1.md`
  - ledger anchor:
    - `BATCH_INDEX__v1.md`

## Quarantine dependency map
- `Q1 REOPEN_ALREADY_CHILD_CLOSED_REFINEDFUEL_PAIR`
  - `BATCH_A2MID_constraints_entropy_chain_fences__v1:MANIFEST.json`
  - `BATCH_A2MID_constraints_foundation_governance_fences__v1:MANIFEST.json`
- `Q2 STALE_QUEUE_TEXT_AS_SELECTION_AUTHORITY`
  - `BATCH_INDEX__v1.md`
- `Q3 UPGRADE_DOC_THREAD_B_CHILD_AS_FULL_COVERAGE_OF_A2FEED_PARENT`
  - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:SELECTION_RATIONALE__v1.md`
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:SOURCE_MAP__v1.md`
- `Q4 DEFAULT_GIANT_SOURCE_MAP_REENTRY_OVER_BOUNDED_ENGINE_PATTERN_SELECTION`
  - `BATCH_INDEX__v1.md`
  - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1:SOURCE_MAP__v1.md`
- `Q5 AUDIT_SELECTION_PACKET_AS_ACTIVE_A2_CONTROL_UPDATE`
  - `A2_MID_REFINEMENT_PROCESS__v1`
  - `BATCH_INDEX__v1.md`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the needed work here was lane-state audit and next-parent selection, not source recovery
  - the paired `Constraints` children plus the ledger and the existing Thread B sibling reduction were sufficient to determine the next bounded target
