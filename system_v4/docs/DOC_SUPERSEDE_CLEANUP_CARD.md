# Doc Supersede Cleanup Card

**Date:** 2026-03-29
**Scope:** Duplicate, superseded, or scratch-level Thread B export surfaces in `system_v4/docs`.
**Rule:** Preserve the newer owner stack. Do not treat staging or audit wrappers as active doctrine.

## 1. Keep

- `THREAD_B_STACK_AUDIT.md` — current stack audit and routing surface for this cluster.
- `THREAD_B_TERM_ADMISSION_MAP.md` — upstream owner packet for term-state staging.
- `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` — current entropy export review surface.
- `THREAD_B_ENTROPY_EXPORT_VALIDATION.md` — current entropy export validation surface.
- `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md` — current thin split export surface for `von_neumann_entropy` + `mutual_information`.
- `THREAD_B_AXIS_MATH_EXPORT_BLOCK_REVIEW.md` — current axis export review surface.
- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md` — keep as the plural candidate staging packet; newer and cleaner than the singular scratch artifact.

## 2. Supersede

- `THREAD_B_ENTROPY_EXPORT_CANDIDATES.md` — superseded by `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` and `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`; already labeled as such.
- `THREAD_B_ENTROPY_EXPORT_PACKET.md` — superseded by `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` and `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`; retain only for audit context.
- `THREAD_B_ENTROPY_MATH_TERM_PACKET.md` — superseded by `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`; older scaffold should not read active.
- `THREAD_B_ENTROPY_MATH_TERM_RUNBOOK.md` — superseded by the stack-audit/admission-map/export-runbook path; already marked stale.
- `THREAD_B_ENTROPY_EXPORT_RUNBOOK.md` — stale runbook; older candidate-export launch surface now sits below the validation/review stack.
- `THREAD_B_EXPORT_BLOCK_REVIEW_RUNBOOK.md` — stale generic runbook; narrower owner-specific review surfaces now exist.
- `THREAD_B_ENTROPY_EXPORT_VALIDATION_RUNBOOK.md` — stale runbook once validation owner packet exists.
- `THREAD_B_ENTROPY_MATH_TERM_ONLY_PACKET.md` — narrower intermediate staging surface now outranked by the split export block plus validation/review stack.
- `THREAD_B_ENTROPY_MATH_TERM_ONLY_RUNBOOK.md` — stale runbook for the intermediate math-term-only packet.
- `THREAD_B_AX1_REVIEW_ONLY_EXPORT_CARD.md` — superseded by `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md`; retain only for audit context.

## 3. Scratch

- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md` — explicit scratch/retracted singular artifact; should not read as an active pipeline surface.
- `AXIS_MATH_BRANCHES_MAP.md` — older broader extraction retained for audit context only; current routing surface is `AXIS_MATH_BRANCH_MAP.md`.

## 4. Unresolved Duplicates

- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md` vs `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md` — singular/plural duplicate family is only partially resolved because the singular file is retracted but still sits beside the kept plural packet.
- `THREAD_B_ENTROPY_EXPORT_RUNBOOK.md`, `THREAD_B_ENTROPY_EXPORT_VALIDATION_RUNBOOK.md`, and `THREAD_B_EXPORT_BLOCK_REVIEW_RUNBOOK.md` — overlapping runbook layer for the same export-review lane; newer owner packets make this runbook stack heavier than needed.
