# Thread B Entropy Split: VN + MI Thin Export Block

**Date:** 2026-03-29
**Lane:** Thread-B/export worker (Claude Code)
**Source:** THREAD_B_STAGING_VALIDATION_PACKET.md §6, task 2
**Authority:** THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md §4 (recommended split)

---

## 1. Why This Split

THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md §4 recommended separating the shared entropy batch into:

1. A thin VN+MI-only block (`von_neumann_entropy` + `mutual_information`)
2. A deferred packet for `conditional_entropy` and `coherent_information`

The reason: `conditional_entropy` is cut-dependent (cut doctrine open). `coherent_information` requires both bridge and cut evidence. These drag the whole batch. VN and MI have no cut dependence and are safe to move independently.

---

## 2. Thin Export Block — VN + MI Only

```text
BEGIN EXPORT_BLOCK v1
EXPORT_ID: ENTROPY_TERMS_BATCH_0001_THIN
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: ENTROPY_TERM_BATCH_VN_MI_REVIEW
STATUS: REVIEW_ONLY — not a submission artifact

REQUIRES BATCH CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
NOTE: This batch is only safe to present after lexeme admission check PASS.
      See THREAD_B_LEXEME_REGISTRY_COLLISION_CHECK.md — 0 hard collisions confirmed.

SPEC_HYP S_MATH_VN_ENTROPY_DEF
SPEC_KIND S_MATH_VN_ENTROPY_DEF CORR MATH_DEF
REQUIRES S_MATH_VN_ENTROPY_DEF CORR LEXEME density_matrix
REQUIRES S_MATH_VN_ENTROPY_DEF CORR LEXEME finite_carrier
DEF_FIELD S_MATH_VN_ENTROPY_DEF CORR OBJECT_FAMILY finite_single_state_entropy
DEF_FIELD S_MATH_VN_ENTROPY_DEF CORR OPERATIONS trace log
DEF_FIELD S_MATH_VN_ENTROPY_DEF CORR INVARIANTS basis_independence single_state_functional
DEF_FIELD S_MATH_VN_ENTROPY_DEF CORR DOMAIN finite_single_state
DEF_FIELD S_MATH_VN_ENTROPY_DEF CORR CODOMAIN scalar
DEF_FIELD S_MATH_VN_ENTROPY_DEF CORR FORMULA "S(rho) = -Tr(rho log rho)"
ASSERT S_MATH_VN_ENTROPY_DEF CORR EXISTS MATH_TOKEN entropy_functional
NOTE: S(rho) is a diagnostic functional. It does not define admissibility.

SPEC_HYP S_TERM_VON_NEUMANN_ENTROPY
SPEC_KIND S_TERM_VON_NEUMANN_ENTROPY CORR TERM_DEF
REQUIRES S_TERM_VON_NEUMANN_ENTROPY CORR S_MATH_VN_ENTROPY_DEF
DEF_FIELD S_TERM_VON_NEUMANN_ENTROPY CORR TERM "von_neumann_entropy"
DEF_FIELD S_TERM_VON_NEUMANN_ENTROPY CORR BINDS S_MATH_VN_ENTROPY_DEF
ASSERT S_TERM_VON_NEUMANN_ENTROPY CORR EXISTS TERM_TOKEN von_neumann_entropy
ASSERT S_TERM_VON_NEUMANN_ENTROPY CORR NOT_EQUAL_TO coherent_information
ASSERT S_TERM_VON_NEUMANN_ENTROPY CORR NOT_EQUAL_TO conditional_entropy

SPEC_HYP S_MATH_MUTUAL_INFORMATION_DEF
SPEC_KIND S_MATH_MUTUAL_INFORMATION_DEF CORR MATH_DEF
REQUIRES S_MATH_MUTUAL_INFORMATION_DEF CORR LEXEME bipartite_density_matrix
REQUIRES S_MATH_MUTUAL_INFORMATION_DEF CORR S_MATH_VN_ENTROPY_DEF
DEF_FIELD S_MATH_MUTUAL_INFORMATION_DEF CORR OBJECT_FAMILY finite_bipartite_correlation
DEF_FIELD S_MATH_MUTUAL_INFORMATION_DEF CORR OPERATIONS partial_trace trace log
DEF_FIELD S_MATH_MUTUAL_INFORMATION_DEF CORR INVARIANTS total_correlation unsigned_functional
DEF_FIELD S_MATH_MUTUAL_INFORMATION_DEF CORR DOMAIN finite_bipartite_state
DEF_FIELD S_MATH_MUTUAL_INFORMATION_DEF CORR CODOMAIN scalar
DEF_FIELD S_MATH_MUTUAL_INFORMATION_DEF CORR FORMULA "I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)"
ASSERT S_MATH_MUTUAL_INFORMATION_DEF CORR EXISTS MATH_TOKEN correlation_functional
NOTE: I(A:B) is unsigned. It does not imply a cut direction or bridge doctrine.

SPEC_HYP S_TERM_MUTUAL_INFORMATION
SPEC_KIND S_TERM_MUTUAL_INFORMATION CORR TERM_DEF
REQUIRES S_TERM_MUTUAL_INFORMATION CORR S_MATH_MUTUAL_INFORMATION_DEF
DEF_FIELD S_TERM_MUTUAL_INFORMATION CORR TERM "mutual_information"
DEF_FIELD S_TERM_MUTUAL_INFORMATION CORR BINDS S_MATH_MUTUAL_INFORMATION_DEF
ASSERT S_TERM_MUTUAL_INFORMATION CORR EXISTS TERM_TOKEN mutual_information
ASSERT S_TERM_MUTUAL_INFORMATION CORR NOT_EQUAL_TO coherent_information

END EXPORT_BLOCK v1
```

---

## 3. What This Block Clears

| Term | Current state in THREAD_B_TERM_ADMISSION_MAP.md | After this block |
|---|---|---|
| `von_neumann_entropy` | TERM_PERMITTED | Still TERM_PERMITTED; MATH_DEF + TERM_DEF wrappers now exist |
| `mutual_information` | TERM_PERMITTED | Same |

Neither term advances to CANONICAL_ALLOWED through this block. The block provides the formal MATH_DEF and TERM_DEF wrapper shapes that were previously absent. Evidence gate for canonical use remains: explicit sim evidence if promoted beyond diagnostic use.

---

## 4. What Stays in the Deferred Packet

| Term | Reason for deferral |
|---|---|
| `conditional_entropy` | Cut-dependent. Cut doctrine open. Requires cut-family typing check before formal MATH_DEF wrapper. |
| `coherent_information` | Bridge + cut evidence both required before any permit path. THREAD_B_SIGNED_AX0_DEFERRED_PACKET.md holds the reserved identifier. |

These must NOT be pulled into this block or any subsequent batch until the controller thread closes bridge/cut doctrine.

---

## 5. Dependency Map

```
finite_carrier (Tier 1 lexeme)
    └── density_matrix (Tier 2 lexeme)
            └── S_MATH_VN_ENTROPY_DEF
                    └── S_TERM_VON_NEUMANN_ENTROPY [von_neumann_entropy]

density_matrix (Tier 2 lexeme)
    └── bipartite_density_matrix (Tier 2 lexeme)
            └── S_MATH_VN_ENTROPY_DEF
                    └── S_MATH_MUTUAL_INFORMATION_DEF
                            └── S_TERM_MUTUAL_INFORMATION [mutual_information]
```

---

## 6. Do Not Smooth

- Do not paste this as a submission artifact.
- Do not add `conditional_entropy` or `coherent_information` to this block.
- Do not treat the wrappers as evidence closure.
- Do not read `unsigned_functional` on MI as a path around the signed cut-entropy problem.
