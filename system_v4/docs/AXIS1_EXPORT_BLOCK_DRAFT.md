# Ax1 Formal Export Block Draft

**Date:** 2026-03-29
**Status:** DRAFT – review‑only (do not promote to CANDIDATE until Ax0 bridge and cut are resolved)

---

## 1. Scope

This block defines the **Ax1** export shape, i.e. the *U‑branch* vs *E‑branch* split that derives from the product of **Ax0** (torus‑entropy field) and **Ax2** (Weyl interaction picture). It is needed as the antecedent for the **Ax4** loop‑commutation export (see `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md`).

NOTE: Ax1 is DERIVED. It must not be treated as a primitive definition.

---

## 2. Formal Definition

```text
BEGIN EXPORT_BLOCK v1
EXPORT_ID: AXIS_MATH_AX1_FORMAL_0001
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: AXIS_MATH_DEF_V1_REVIEW
PERMIT_STATE: REVIEW_ONLY
CONTENT:

SPEC_HYP S_MATH_AX1_BRANCH_DEF
SPEC_KIND S_MATH_AX1_BRANCH_DEF CORR MATH_DEF

# Branch objects – derived from Ax0 × Ax2
DEF_FIELD S_MATH_AX1_BRANCH_DEF CORR OBJECTS Ax0 Ax2

# Logical split based on the Ax0 bit and the Ax2 frame class
DEF_FIELD S_MATH_AX1_BRANCH_DEF CORR LOGIC "b1 = f(b0, ax2): U if (b0 = -1 AND ax2 = direct) OR (b0 = +1 AND ax2 = conjugated); NU otherwise"

# Invariant – Ax1 is derived from Ax0 hemisphere state crossed with Ax2 frame class
DEF_FIELD S_MATH_AX1_BRANCH_DEF CORR INVARIANT "Ax1 is derived from the Ax0 bit b0 crossed with Ax2 frame class; it must not be defined by duplicating the continuous eta seat"

# Reference to underlying primitives
REQUIRES S_MATH_AX1_BRANCH_DEF CORR Ax0
REQUIRES S_MATH_AX1_BRANCH_DEF CORR Ax2

# Term definition for downstream use
SPEC_HYP S_TERM_AX1_BRANCH_TERM
SPEC_KIND S_TERM_AX1_BRANCH_TERM CORR TERM_DEF
REQUIRES S_TERM_AX1_BRANCH_TERM CORR S_MATH_AX1_BRANCH_DEF
DEF_FIELD S_TERM_AX1_BRANCH_TERM CORR TERM "axis1_branch"
DEF_FIELD S_TERM_AX1_BRANCH_TERM CORR BINDS S_MATH_AX1_BRANCH_DEF
ASSERT S_TERM_AX1_BRANCH_TERM CORR EXISTS TERM_TOKEN unitary_branch
ASSERT S_TERM_AX1_BRANCH_TERM CORR EXISTS TERM_TOKEN proper_cptp_branch

END EXPORT_BLOCK
```

---

## 3. Evidence Registry (currently none)

*The block is **review‑only** until the Ax0 bridge (`Xi`) and cut (`A|B`) are resolved. Once those are settled, the above definition can be promoted to `CANDIDATE` and then to `ENFORCEMENT`.*

---

## 4. Dependencies

- **Ax0**: `THREAD_B_AXIS_MATH_EXPORT_BLOCK_REVIEW.md` (geometric diagnostics)
- **Ax2**: `AXIS_3_4_5_6_QIT_MATH.md` (Weyl interaction picture)
- **Lexeme**: `finite_scalar_encoding`, `non_commutativity` (Tier‑1 root‑earned lexemes)

---

## 5. Next Actions

1. **Review**: Ensure the derivation rule matches the current `b1 = f(b0, ax2)` read in `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md`.
2. **Validate**: Run a quick simulation (`sim_axis1_branch_test.py`) that computes `b0` plus the Ax2 frame class and checks the branch assignment.
3. **Submit**: Keep this draft review-only until the stronger review block is accepted; do not promote directly from this draft.

---

*Do not modify any locked axis definitions or bridge/cut contracts while this block is in review.*
