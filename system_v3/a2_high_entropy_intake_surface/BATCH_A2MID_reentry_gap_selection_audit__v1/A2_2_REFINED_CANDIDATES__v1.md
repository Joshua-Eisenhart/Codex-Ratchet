# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_reentry_gap_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `CURRENT_REENTRY_PAIR_IS_DIRECT_CHILD_CLOSED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current refined-fuel re-entry pair is closed at the direct-child level:
  - `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`
    already has `BATCH_A2MID_constraints_entropy_chain_fences__v1`
  - `BATCH_refinedfuel_constraints_term_conflict__v1`
    already has `BATCH_A2MID_constraints_foundation_governance_fences__v1`

Why this survives reduction:
- it prevents pointless reopening of just-completed sibling parents
- it turns local queue cleanup into one reusable lane-closure rule

Source lineage:
- parent child packet:
  - `BATCH_A2MID_constraints_entropy_chain_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
- parent child packet:
  - `BATCH_A2MID_constraints_foundation_governance_fences__v1:DOWNSTREAM_CONSEQUENCE_NOTES__v1.md`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim the entire unresolved queue is closed
- it preserves only closure of the current local refined-fuel pair

## Candidate RC2) `LEDGER_STATE_OVERRIDES_STALE_QUEUE_TEXT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- next-target selection should follow current ledger state rather than stale queue text that still points at already-child-covered parents

Why this survives reduction:
- the thread needed one explicit rule for choosing the next unresolved parent after local child completion
- it keeps the A2-mid lane repo-led instead of conversation-led

Source lineage:
- parent child packet:
  - `BATCH_A2MID_constraints_entropy_chain_fences__v1:SELECTION_RATIONALE__v1.md`
- parent child packet:
  - `BATCH_A2MID_constraints_foundation_governance_fences__v1:SELECTION_RATIONALE__v1.md`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim every older queue decision was wrong
- it preserves only the rule that current ledger state wins when queue text and child coverage diverge

## Candidate RC3) `NEXT_REAL_UNRESOLVED_PARENT_IS_A2FEED_THREAD_B_BOOTPACK_KERNEL`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest current next unresolved parent is:
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1`
- why this one:
  - unresolved with no direct child
  - compact formal engine-pattern parent
  - high-value fail-closed kernel and term-admission seam
  - clearer bounded next step than giant source-map revisits

Why this survives reduction:
- it packages the actual next-target choice into one explicit reusable selection packet
- it keeps the next `go on` source-led and narrow

Source lineage:
- comparison anchors:
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:SOURCE_MAP__v1.md`
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:A2_3_DISTILLATES__v1.md`
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:MANIFEST.json`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not promote the selected parent into A2-1 law
- it preserves only next-target priority for later bounded reduction

## Candidate RC4) `UPGRADE_DOC_THREAD_B_CHILD_IS_ADDITIVE_NOT_DUPLICATIVE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the existing Thread B child
  - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1`
  does not close the a2feed Thread B parent
- it remains useful as sibling context because:
  - it comes from the upgrade-doc Thread B parent
  - it narrows duplicate-copy, tag, namespace, and handler drift in a different source family
  - the a2feed parent still carries its own version-mismatch and derived-only-kernel lineage

Why this survives reduction:
- it blocks a false closure read on the next selected parent
- it preserves the additive value of the existing upgrade-doc child without collapsing the two families together

Source lineage:
- comparison anchor:
  - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:SOURCE_DEPENDENCY_MAP__v1.md`
- comparison anchor:
  - `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:A2_2_REFINED_CANDIDATES__v1.md`
- comparison anchor:
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:A2_3_DISTILLATES__v1.md`

Preserved limits:
- this batch does not merge the two Thread B parents into one canonical source
- it preserves only the rule that the existing child is additive sibling context

## Candidate RC5) `COMPACT_ENGINE_PATTERN_REENTRY_BEATS_GIANT_SOURCE_MAP_REVISITS`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- when several unresolved parents remain, the next bounded step should prefer the compact unresolved engine-pattern parent over giant high-entropy source-map or archive-package revisits

Why this survives reduction:
- it converts the audit result into one practical prioritization rule
- it keeps the lane moving on the highest-yield unresolved seam

Source lineage:
- comparison anchor:
  - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1:SOURCE_MAP__v1.md`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not declare giant unresolved parents unimportant
- it preserves only the bounded next-step priority rule

## Quarantined Residue Q1) `REOPEN_ALREADY_CHILD_CLOSED_REFINEDFUEL_PAIR`
Status:
- `QUARANTINED`

Preserved residue:
- reopening the paired `Constraints` parents again immediately
- acting as if the two fresh child reductions did not change lane state

Why it stays quarantined:
- the audit shows those two parents are already directly covered by stronger child reductions
- reopening them now would repeat work rather than expose a real new gap

Source lineage:
- `BATCH_A2MID_constraints_entropy_chain_fences__v1:MANIFEST.json`
- `BATCH_A2MID_constraints_foundation_governance_fences__v1:MANIFEST.json`

## Quarantined Residue Q2) `STALE_QUEUE_TEXT_AS_SELECTION_AUTHORITY`
Status:
- `QUARANTINED`

Preserved residue:
- choosing the next target from older queue text alone even after ledger state has changed

Why it stays quarantined:
- current A2-mid selection must remain repo-led and child-coverage-aware
- stale queue text is a thread artifact, not the stronger state surface

Source lineage:
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q3) `UPGRADE_DOC_THREAD_B_CHILD_AS_FULL_COVERAGE_OF_A2FEED_PARENT`
Status:
- `QUARANTINED`

Preserved residue:
- treating the existing upgrade-doc Thread B child as if it already closes the a2feed Thread B parent

Why it stays quarantined:
- the source families and direct parents differ
- the existing child is informative, but it does not erase the unresolved a2feed parent

Source lineage:
- `BATCH_A2MID_bootpack_thread_b_kernel_gating__v1:SELECTION_RATIONALE__v1.md`
- `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1:SOURCE_MAP__v1.md`

## Quarantined Residue Q4) `DEFAULT_GIANT_SOURCE_MAP_OR_ARCHIVE_PACKAGE_REENTRY`
Status:
- `QUARANTINED`

Preserved residue:
- jumping next to Leviathan, GPT trigram, megaboot, or archive-package revisits simply because they are older or larger

Why it stays quarantined:
- the audit result is about bounded next-step yield, not seniority or bulk
- the compact unresolved Thread B kernel parent is the cleaner immediate reduction target

Source lineage:
- `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1:SOURCE_MAP__v1.md`
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q5) `AUDIT_SELECTION_PACKET_AS_ACTIVE_A2_CONTROL_UPDATE`
Status:
- `QUARANTINED`

Preserved residue:
- treating this audit packet as if it directly mutates active A2 control memory

Why it stays quarantined:
- this batch is only a bounded intake-surface selection artifact
- active A2 promotion still requires a later explicit control pass

Source lineage:
- `A2_MID_REFINEMENT_PROCESS__v1`
- `BATCH_INDEX__v1.md`
