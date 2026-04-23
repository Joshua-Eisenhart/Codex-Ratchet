# Return Packet: Duplicate Family Collapse Plan

**Date:** 2026-03-29
**Agent:** Claude Sonnet 4.7
**Status:** COMPLETE (Plan Only)

## 1. Executive Summary
This return packet executes the requirement to produce an aggressive but safe plan to collapse redundant, stale, and duplicate document families in the `system_v4` documentation stack. In strict accordance with the rules, it does not mandate file deletion or alter doctrine ranking. It simply classifies existing files into one of four states: **keep**, **supersede**, **scratch**, or **archive_only**, based directly on the authoritative rankings in `CURRENT_AUTHORITATIVE_STACK_INDEX.md` and the existing files in `system_v4/docs/`.

## 2. Duplicate Family Collapses

### Family 1: Axis Math Export Candidacy
*Overlap: Plural staging lists vs. singular scratch files left unresolved.*
* **keep**: `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md` (Active Thread B staging surface).
* **scratch**: `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md` (Explicitly listed as retracted in the index; resolves the open duplicate item).

### Family 2: Axis Math Branch Maps
*Overlap: Root naming collision creating ambiguity on the active route map.*
* **keep**: `AXIS_MATH_BRANCH_MAP.md` (Documented in the index as the active routing-only support surface).
* **supersede**: `AXIS_MATH_BRANCHES_MAP.md` (Naming-level duplicate risk, to be superseded to eliminate confusion).

### Family 3: Thread B Entropy Export & Validation History
*Overlap: A long tail of intermediate states outranked by the current VN/MI split and block review surfaces.*
* **keep**: `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md` (Active preferred entropy export surface).
* **keep**: `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` (Background entropy audit lineage).
* **keep**: `THREAD_B_ENTROPY_EXPORT_VALIDATION.md` (Current validation surface).
* **supersede**: `THREAD_B_ENTROPY_EXPORT_CANDIDATES.md` (Superseded by split export).
* **supersede**: `THREAD_B_ENTROPY_EXPORT_PACKET.md` (Superseded by split export and block review).
* **supersede**: `THREAD_B_ENTROPY_MATH_TERM_PACKET.md` (Superseded by split export).
* **supersede**: `THREAD_B_ENTROPY_MATH_TERM_ONLY_PACKET.md` (Intermediate packet, superseded by split export).

### Family 4: Thread B Runbook Layer
*Overlap: Generic legacy instruction layers superseded by narrower owner-specific review and admission surfaces.*
* **archive_only**: `THREAD_B_ENTROPY_EXPORT_RUNBOOK.md` 
* **archive_only**: `THREAD_B_ENTROPY_EXPORT_VALIDATION_RUNBOOK.md`
* **archive_only**: `THREAD_B_EXPORT_BLOCK_REVIEW_RUNBOOK.md`
* **archive_only**: `THREAD_B_ENTROPY_MATH_TERM_RUNBOOK.md`
* **archive_only**: `THREAD_B_ENTROPY_MATH_TERM_ONLY_RUNBOOK.md`
* **archive_only**: `THREAD_B_TERM_ADMISSION_RUNBOOK.md` (Overlapping legacy runbook given the existence of `THREAD_B_TERM_ADMISSION_MAP.md` as the staging owner packet).

### Family 5: Thread B Ax1 Export Review
*Overlap: Unindexed singular card overlapping the canonical block review.*
* **keep**: `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md` (Listed as active review-only Ax1 antecedent).
* **supersede**: `THREAD_B_AX1_REVIEW_ONLY_EXPORT_CARD.md` (Unlisted duplicate to be superseded into the canon block review file).

### Family 6: Proto-Ratchet vs. Ax0 Constraint Geometry (Unindexed Legacy)
*Overlap: Early "Proto Ratchet" and unindexed Ax0 geometry constraint explorations overlapping the formal `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION` surface space.*
* **keep**: `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md` (Confirmed Ax0 doctrine owner).
* **keep**: `AXIS0_GEOMETRIC_CONSTRAINT_MANIFOLD.md` (Confirmed active support surface).
* **supersede**: `AXIS0_GEOMETRIC_CONSTRAINT_MANIFOLD_OPTIONS.md`
* **supersede**: `AXIS0_GEOMETRIC_CONSTRAINT_OPTIONS.md`
* **supersede**: `AXIS0_GEOMETRIC_CONSTRAINT_PACKET.md`
* **archive_only**: `PROTO_RATCHET_CONSTRAINT_GEOMETRY_BASIN.md`
* **archive_only**: `PROTO_RATCHET_GEOMETRY_HANDOFF_CARD.md`

## 3. Recommended Next Actions
1. Apply internal `[Superseded]`, `[Archived]`, and `[Scratch]` banners to the relevant target files without removing them from the filesystem.
2. Update the `DOC_SUPERSEDE_CLEANUP_CARD.md` once these banners have been safely appended, permanently resolving Section 4.3 of the Master Index.
