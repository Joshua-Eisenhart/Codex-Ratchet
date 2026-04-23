# Duplicate Family Audit Result

**Date:** 2026-03-29
**Audit Scope:** system_v4/docs directory
**Classification scheme:** `keep` / `supersede` / `scratch` / `archive_only`
**Doctrine changes:** None. Direct pass-through classification.

## 1. Singular/Plural Duplicates

- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md` -> `scratch`
- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md` -> `keep`

- `AXIS_MATH_BRANCHES_MAP.md` -> `supersede`
- `AXIS_MATH_BRANCH_MAP.md` -> `keep`

## 2. Stale Runbooks vs Keep Runbooks

- `THREAD_B_ENTROPY_MATH_TERM_RUNBOOK.md` -> `supersede`
- `THREAD_B_ENTROPY_EXPORT_RUNBOOK.md` -> `supersede`
- `THREAD_B_EXPORT_BLOCK_REVIEW_RUNBOOK.md` -> `supersede`
- `THREAD_B_ENTROPY_EXPORT_VALIDATION_RUNBOOK.md` -> `supersede`
- `THREAD_B_ENTROPY_MATH_TERM_ONLY_RUNBOOK.md` -> `supersede`

- `THREAD_B_TERM_ADMISSION_RUNBOOK.md` -> `keep`
- `THREAD_B_CONSTRAINT_AUTORESEARCH_RUNBOOK.md` -> `keep`
- `THREAD_B_ROOT_CONSTRAINTS_AUTORESEARCH_RUNBOOK.md` -> `keep`
- `AXIS0_CUT_ONLY_AUTORESEARCH_RUNBOOK.md` -> `keep`

## 3. Superseded Packet Families

- `THREAD_B_ENTROPY_EXPORT_CANDIDATES.md` -> `supersede`
- `THREAD_B_ENTROPY_EXPORT_PACKET.md` -> `supersede`
- `THREAD_B_ENTROPY_MATH_TERM_PACKET.md` -> `supersede`
- `THREAD_B_ENTROPY_MATH_TERM_ONLY_PACKET.md` -> `supersede`

## 4. Archive Only

- `AXES_0_12_LEGACY_CENSUS.md` -> `archive_only`

## 5. Active Doctrine (Keep)

The following core index/support documents are retained as the live structure:
- `CURRENT_AUTHORITATIVE_STACK_INDEX.md` -> `keep`
- `THREAD_CONSOLIDATION_CONTROLLER.md` -> `keep`
- `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md` -> `keep`
- `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md` -> `keep`
- `AXIS0_CUT_TAXONOMY.md` -> `keep`
- `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md` -> `keep`
- `THREAD_B_STACK_AUDIT.md` -> `keep`
- `THREAD_B_LANE_HANDOFF_PACKET.md` -> `keep`
- `DOC_SUPERSEDE_CLEANUP_CARD.md` -> `keep`
*(All other unlisted documents currently designated authority/support in the CURRENT_AUTHORITATIVE_STACK_INDEX.md are also implicitly `keep`.)*
