# Thread B Ax1 Review-Only Export Card

**Date:** 2026-03-29
**Status:** SUPERSEDED. Smaller Ax1 review-only card retained for audit context only. Prefer the fuller review block.
**Superseded by:** [THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md).
**Previous review level:** REVIEW_ONLY
**Purpose:** smallest Ax1 `MATH_DEF + TERM_DEF` surface needed to unblock Ax4 antecedent language while keeping Ax1 derived from `Ax0 x Ax2`.

---

## 1. Candidate MATH_DEF id

| Field | Value |
|---|---|
| **ID** | `S_MATH_AX1_BRANCH_CLASS_DEF` |
| **Kind** | `MATH_DEF` |
| **Object family** | finite derived branch-class family |
| **Derivation rule** | `Ax1 = f(Ax0, Ax2)` with `U` branch = `{Se, Ni}` and `NU` branch = `{Ne, Si}` |
| **Antecedent use** | supplies the minimal `U` / `NU` branch partition that Ax4 cites when stating `UEUE` vs `EUEU` ordering |

---

## 2. Candidate TERM_DEF id

| Field | Value |
|---|---|
| **ID** | `S_TERM_AX1_BRANCH_CLASS` |
| **Kind** | `TERM_DEF` |
| **Term** | `axis1_branch_class` |
| **Binds** | `S_MATH_AX1_BRANCH_CLASS_DEF` |
| **Scope** | generic Ax1 branch label only; does not separately promote `unitary_branch` or `proper_cptp_branch` |

---

## 3. Dependencies

| Dependency | Why it is required |
|---|---|
| `system_v4/docs/AXIS_0_1_2_QIT_MATH.md` | provides the locked `Ax0` / `Ax2` terrain basis and the reduced `Ax1 x Ax2` terrain join context |
| `system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md` | states that `Ax1` is locked as derived from `Ax0 x Ax2` and gives the Ax4 `U`/`E` antecedent usage |
| `system_v4/docs/AXIS_PRIMITIVE_DERIVED.md` | explicitly fixes `Ax1` as derived, not primitive, and gives the cross-diagonal split `Se/Ni` vs `Ne/Si` |
| `system_v4/docs/THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md` | records that Ax4 still depends on later Ax1 support work |
| `system_v4/docs/THREAD_B_AXIS_MATH_EXPORT_BLOCK_REVIEW.md` | records the same open Ax4 dependency and the need for a cleaner Ax1 antecedent handoff |
| `system_v4/docs/THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md` | upstream fuller review draft from which this smaller review-only card is reduced |

---

## 4. Why It Remains Review-Only

- Ax1 is a derived closure from `Ax0 x Ax2`, so this card must not be read as a primitive axis definition.
- The card exists only to supply minimal antecedent language for Ax4; it does not authorize Ax4 promotion.
- The card avoids `CANON_PERMIT`, export-block submission framing, and any claim that branch terminology is admitted beyond review.
- The card does not reopen or modify locked `Ax0`, `Ax2`, `Ax3`, `Ax4`, `Ax5`, or `Ax6` definitions.
- The card deliberately stops at one generic `TERM_DEF` so the antecedent can be cited without promoting extra Ax1-side vocabulary.
