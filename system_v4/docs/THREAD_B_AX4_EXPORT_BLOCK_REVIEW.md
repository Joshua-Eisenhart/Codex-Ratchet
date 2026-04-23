# Thread B Ax4 Export Block Review — Loop Ordering Non-Commutativity

**Date:** 2026-03-29
**Lane:** Thread-B/export worker (Claude Code)
**Status:** REVIEW_ONLY — do not promote or submit
**Antecedent required:** THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md (AX1_BRANCH_DERIVATION_REVIEW_0001)

---

## 1. Ax4 Definition

**From AXIS_3_4_5_6_QIT_MATH.md (locked):**

Ax4 distinguishes the CPTP semigroup composition ordering within one engine cycle. The two orderings are non-commutative:

- **Deductive** (fiber/inner, b₃ = −1): Φ_UEUE = U∘E∘U∘E — FeTi kernel
- **Inductive** (base/outer, b₃ = +1): Φ_EUEU = E∘U∘E∘U — TeFi kernel

Where:
- U = Ne/Si class (NU/unitary branch, Ax1)
- E = Se/Ni class (U/dissipative branch, Ax1)

**Ax4 is derived** from Ax3 (fiber vs base loop type, b₃) and the engine composition rule. It is not a primitive axis.

---

## 2. Evidence Anchors

All evidence is emitted by `sim_Ax4_commutation.py` — PASS ✓ (run 2026-03-29).

| Token | Witness | Value |
|---|---|---|
| `AX4_UEUE_EUEU_DISTINCT` | non_trivial_distance_count=7/8 | PASS |
| `AX4_ENTROPY_TRAJECTORY_DIFFERS` | max_traj_diff > 0.01 | PASS |
| `AX4_LOOP_ORDERING_NONCOMMUTATIVE` | robustness_rate ≥ 0.95 | PASS |
| `AX4_UE_COMMUTATOR_NONZERO` | D(U∘E, E∘U) > 1e-4 | PASS |

---

## 3. Export Block Draft

```text
BEGIN EXPORT_BLOCK v1
EXPORT_ID: AX4_LOOP_ORDERING_REVIEW_0001
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: AX4_LOOP_ORDERING_REVIEW
STATUS: REVIEW_ONLY — not a submission artifact

REQUIRES BLOCK CORR AX1_BRANCH_DERIVATION_REVIEW_0001
REQUIRES BLOCK CORR AX3_MANIFOLD_PATH_REVIEW
NOTE: Ax4 is DERIVED from Ax3 (loop type b3) and Ax1 (U/NU branch assignment).
      It must not be treated as a primitive definition.
NOTE: The shorthand letters `U` and `E` in this review block are local ordering labels only.
      They do not rename or outrank the underlying Ax1 branch-class terms.
NOTE: Any stronger engine-composition dependency remains controller-open until
      it has an explicit owner surface; this block must not smuggle it in as a primitive axiom.

SPEC_HYP S_MATH_AX4_LOOP_ORDER_CLASS
SPEC_KIND S_MATH_AX4_LOOP_ORDER_CLASS CORR MATH_DEF
REQUIRES S_MATH_AX4_LOOP_ORDER_CLASS CORR LEXEME CPTP_semigroup
REQUIRES S_MATH_AX4_LOOP_ORDER_CLASS CORR LEXEME Channel_composition
REQUIRES S_MATH_AX4_LOOP_ORDER_CLASS CORR LEXEME non_commutativity
REQUIRES S_MATH_AX4_LOOP_ORDER_CLASS CORR S_MATH_AX1_BRANCH_CLASS
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR OBJECT_FAMILY cptp_composition_order
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR OPERATIONS channel_composition operator_application
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR INVARIANTS binary_partition non_commutative_under_swap
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR DOMAIN loop_family
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR CODOMAIN ordering_label
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR DEDUCTIVE_ORDERING "Phi_UEUE = U∘E∘U∘E (fiber/inner, b3=-1)"
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR INDUCTIVE_ORDERING "Phi_EUEU = E∘U∘E∘U (base/outer, b3=+1)"
DEF_FIELD S_MATH_AX4_LOOP_ORDER_CLASS CORR NONCOMMUTATIVITY "Phi_UEUE != Phi_EUEU for non-trivial input states"
ASSERT S_MATH_AX4_LOOP_ORDER_CLASS CORR EXISTS MATH_TOKEN loop_composition_order
ASSERT S_MATH_AX4_LOOP_ORDER_CLASS CORR DERIVED_FROM Ax3_loop_type Ax1_branch_class
ASSERT S_MATH_AX4_LOOP_ORDER_CLASS CORR EVIDENCE AX4_LOOP_ORDERING_NONCOMMUTATIVE=PASS
ASSERT S_MATH_AX4_LOOP_ORDER_CLASS CORR EVIDENCE AX4_UEUE_EUEU_DISTINCT=PASS

SPEC_HYP S_TERM_LOOP_ORDER_UNITARY_FIRST
SPEC_KIND S_TERM_LOOP_ORDER_UNITARY_FIRST CORR TERM_DEF
REQUIRES S_TERM_LOOP_ORDER_UNITARY_FIRST CORR S_MATH_AX4_LOOP_ORDER_CLASS
DEF_FIELD S_TERM_LOOP_ORDER_UNITARY_FIRST CORR TERM "loop_order_unitary_first"
DEF_FIELD S_TERM_LOOP_ORDER_UNITARY_FIRST CORR BINDS S_MATH_AX4_LOOP_ORDER_CLASS
DEF_FIELD S_TERM_LOOP_ORDER_UNITARY_FIRST CORR SELECTOR "UEUE ordering: fiber/inner (b3=-1, deductive)"
ASSERT S_TERM_LOOP_ORDER_UNITARY_FIRST CORR EXISTS TERM_TOKEN loop_order_unitary_first
ASSERT S_TERM_LOOP_ORDER_UNITARY_FIRST CORR EVIDENCE AX4_UEUE_EUEU_DISTINCT=PASS

SPEC_HYP S_TERM_LOOP_ORDER_NONUNITARY_FIRST
SPEC_KIND S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR TERM_DEF
REQUIRES S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR S_MATH_AX4_LOOP_ORDER_CLASS
DEF_FIELD S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR TERM "loop_order_nonunitary_first"
DEF_FIELD S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR BINDS S_MATH_AX4_LOOP_ORDER_CLASS
DEF_FIELD S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR SELECTOR "EUEU ordering: base/outer (b3=+1, inductive)"
ASSERT S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR EXISTS TERM_TOKEN loop_order_nonunitary_first
ASSERT S_TERM_LOOP_ORDER_NONUNITARY_FIRST CORR EVIDENCE AX4_LOOP_ORDERING_NONCOMMUTATIVE=PASS

END EXPORT_BLOCK v1
```

---

## 4. Dependency Map

```
non_commutativity (Tier 1 lexeme, ROOT_EARNED)
    └── CPTP_semigroup (Tier 2 lexeme)
    └── Channel_composition (Tier 2 lexeme)

S_MATH_AX1_BRANCH_CLASS (AX1_BRANCH_DERIVATION_REVIEW_0001)
    └── S_MATH_AX4_LOOP_ORDER_CLASS
            ├── S_TERM_LOOP_ORDER_UNITARY_FIRST [loop_order_unitary_first]
            └── S_TERM_LOOP_ORDER_NONUNITARY_FIRST [loop_order_nonunitary_first]
```

---

## 5. What This Unblocks

| Blocked item | Why unblocked |
|---|---|
| `loop_order_unitary_first` + `loop_order_nonunitary_first` canonicalization path | MATH_DEF wrapper now exists; terms had evidence tokens but no formal wrapper |
| Any Ax4-dependent downstream block | Can cite `AX4_LOOP_ORDERING_REVIEW_0001` as antecedent |

---

## 6. What This Does Not Do

- Does not promote `loop_order_unitary_first` or `loop_order_nonunitary_first` to CANONICAL_ALLOWED
- Does not make Ax4 a primitive axis — it is derived
- Does not affect Ax0, Ax1, Ax2, Ax3 definitions (all locked or review-only)
- Does not introduce `engine_composition_rule` as a closed primitive dependency
- Does not close the bridge/cut open issue

---

## 7. Do Not Smooth

- Do not treat this as an Ax4 primitive definition.
- Do not let local `U` / `E` ordering shorthand drift into branch renaming outside this block.
- Do not cite this block as promotion evidence for any axis.
- Do not let the evidence tokens (PASS on sim) be read as canonical admission.
- Stay at REVIEW_ONLY until controller confirms Ax4 is ready for promotion consideration.
