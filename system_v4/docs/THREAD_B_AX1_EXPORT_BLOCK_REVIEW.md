# Thread B Ax1 Export Block Review — U/NU Branch Derivation

**Date:** 2026-03-29
**Lane:** Thread-B/export worker (Claude Code)
**Source:** THREAD_B_STAGING_VALIDATION_PACKET.md §6, task 3
**Status:** REVIEW_ONLY — draft MATH_DEF + TERM_DEF shapes; do not promote or submit

---

## 1. Why Ax1 First

Ax4's export block lists Ax1 as an antecedent (Ax4 claims the UEUE/EUEU ordering follows the U/NU branch classification). The Ax4 review shape cannot be safely cited until Ax1 has at minimum a formal MATH_DEF + TERM_DEF review shape. This block provides that shape and nothing more.

---

## 2. The Ax1 Derivation

**From TERRAIN_LAW_LEDGER.md and AXIS_PRIMITIVE_DERIVED.md:**

Ax1 is **derived** (not primitive). It follows from:

- **Ax0** (hemisphere threshold b₀ = sgn(r_z)): identifies N-type vs S-type terrain families
- **Ax2** (Weyl interaction picture): identifies direct vs conjugated representation frames

The derived rule: the U/NU split tracks which terrain type couples to a dissipative channel vs a unitary channel in the subcycle.

| Terrain | Ax0 (b₀) | Ax2 (frame) | Ax1 class |
|---|---|---|---|
| Se | -1 (S) | direct | U (dissipative branch) |
| Ni | +1 (N) | conjugated | U (dissipative branch) |
| Ne | +1 (N) | direct | NU (unitary branch) |
| Si | -1 (S) | conjugated | NU (unitary branch) |

The U class = {Se, Ni}; NU class = {Ne, Si}. The grouping is: U terrain = direct(S) ∪ conjugated(N); NU terrain = direct(N) ∪ conjugated(S). This is consistent with Ax6 b₆ = -b₀·b₃ and the 64-address audit.

---

## 3. Export Block Draft

```text
BEGIN EXPORT_BLOCK v1
EXPORT_ID: AX1_BRANCH_DERIVATION_REVIEW_0001
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: AX1_BRANCH_DERIVATION_REVIEW
STATUS: REVIEW_ONLY — antecedent shape for Ax4 block; not a submission artifact

REQUIRES BLOCK CORR AX0_PRIMITIVE_DEFINITION
REQUIRES BLOCK CORR AX2_INTERACTION_PICTURE_DEFINITION
NOTE: Ax1 is DERIVED. It must not be treated as a primitive definition.
      Its MATH_DEF is the derivation rule, not an independent constraint.
NOTE: This block does not resolve any Ax0 bridge/cut question.
      It stays valid only as a review-layer antecedent while bridge/cut doctrine remains open.
NOTE: Generator-family evidence remains required before `unitary_branch` or
      `proper_cptp_branch` can move beyond REVIEW_ONLY / TERM_PERMITTED use.

SPEC_HYP S_MATH_AX1_BRANCH_CLASS
SPEC_KIND S_MATH_AX1_BRANCH_CLASS CORR MATH_DEF
REQUIRES S_MATH_AX1_BRANCH_CLASS CORR LEXEME density_matrix
REQUIRES S_MATH_AX1_BRANCH_CLASS CORR LEXEME CPTP_channel
REQUIRES S_MATH_AX1_BRANCH_CLASS CORR LEXEME Lindblad_generator
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR OBJECT_FAMILY terrain_generator_branch
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR OPERATIONS subcycle_operator_application
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR INVARIANTS binary_partition two_classes
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR DOMAIN terrain_family
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR CODOMAIN branch_label
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR DERIVATION_RULE "b1 = f(b0, ax2): U if (b0=-1 AND ax2=direct) OR (b0=+1 AND ax2=conjugated); NU otherwise"
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR U_CLASS "Se, Ni — dissipative channel generators in subcycle"
DEF_FIELD S_MATH_AX1_BRANCH_CLASS CORR NU_CLASS "Ne, Si — unitary channel generators in subcycle"
ASSERT S_MATH_AX1_BRANCH_CLASS CORR EXISTS MATH_TOKEN terrain_branch_partition
ASSERT S_MATH_AX1_BRANCH_CLASS CORR DERIVED_FROM Ax0_hemisphere_threshold Ax2_weyl_frame
NOTE: `U_CLASS` and `NU_CLASS` are branch-class selectors in this review block.
      Do not read them as primitive terrain identities or canon position classes.

SPEC_HYP S_TERM_UNITARY_BRANCH
SPEC_KIND S_TERM_UNITARY_BRANCH CORR TERM_DEF
REQUIRES S_TERM_UNITARY_BRANCH CORR S_MATH_AX1_BRANCH_CLASS
DEF_FIELD S_TERM_UNITARY_BRANCH CORR TERM "unitary_branch"
DEF_FIELD S_TERM_UNITARY_BRANCH CORR BINDS S_MATH_AX1_BRANCH_CLASS
DEF_FIELD S_TERM_UNITARY_BRANCH CORR SELECTOR "NU class: Ne, Si"
ASSERT S_TERM_UNITARY_BRANCH CORR EXISTS TERM_TOKEN unitary_branch
NOTE: "unitary_branch" = NU class. Name is from THREAD_B_TERM_ADMISSION_MAP.md — no renaming.

SPEC_HYP S_TERM_PROPER_CPTP_BRANCH
SPEC_KIND S_TERM_PROPER_CPTP_BRANCH CORR TERM_DEF
REQUIRES S_TERM_PROPER_CPTP_BRANCH CORR S_MATH_AX1_BRANCH_CLASS
DEF_FIELD S_TERM_PROPER_CPTP_BRANCH CORR TERM "proper_cptp_branch"
DEF_FIELD S_TERM_PROPER_CPTP_BRANCH CORR BINDS S_MATH_AX1_BRANCH_CLASS
DEF_FIELD S_TERM_PROPER_CPTP_BRANCH CORR SELECTOR "U class: Se, Ni"
ASSERT S_TERM_PROPER_CPTP_BRANCH CORR EXISTS TERM_TOKEN proper_cptp_branch
NOTE: "proper_cptp_branch" = U class. Name is from THREAD_B_TERM_ADMISSION_MAP.md.

END EXPORT_BLOCK v1
```

---

## 4. What This Unblocks

| Blocked item | Why unblocked |
|---|---|
| Ax4 export block antecedent | Ax4's `REQUIRES ... CORR AX1_BRANCH_DERIVATION` can now point to `AX1_BRANCH_DERIVATION_REVIEW_0001` instead of informal derivation note |
| `unitary_branch` + `proper_cptp_branch` canonicalization path | MATH_DEF wrapper now exists; terms were TERM_PERMITTED without a formal wrapper |

---

## 5. What This Does Not Do

- Does not promote `unitary_branch` or `proper_cptp_branch` to CANONICAL_ALLOWED
- Does not satisfy the generator-family evidence gate required before any future promotion
- Does not introduce Ax1 as a primitive axis (it is derived)
- Does not affect Ax0, Ax2, or any other axis definition (all locked)
- Does not resolve the bridge/cut open issue — Ax1 derivation is independent of bridge/cut

---

## 6. Derivation Consistency Check

Cross-check against 64-address audit (64-address audit table from `sim_64_address_audit.py`):

| Terrain | b₀ | Ax2 | Ax1 rule yields | Matches TERRAIN_LAW_LEDGER.md |
|---|---|---|---|---|
| Se | -1 | 0 (direct) | U | U ✓ |
| Ne | +1 | 0 (direct) | NU | NU ✓ |
| Ni | +1 | 1 (conjugated) | U | U ✓ |
| Si | -1 | 1 (conjugated) | NU | NU ✓ |

All 4 terrain assignments consistent. Derivation rule is internally sound.

---

## 7. Do Not Smooth

- Do not treat this as an Ax1 primitive definition — Ax1 is derived.
- Do not cite this block as evidence for Ax4 promotion (it's only a review shape).
- Do not reopen Ax0 or Ax2 definitions through this block.
- Do not treat `U_CLASS` / `NU_CLASS` selectors as if they were primitive terrain identities.
- Do not let `unitary_branch`/`proper_cptp_branch` TERM_DEF wrappers be read as CANONICAL_ALLOWED.
- Stay at REVIEW_ONLY until controller confirms Ax1 is ready for promotion consideration.
