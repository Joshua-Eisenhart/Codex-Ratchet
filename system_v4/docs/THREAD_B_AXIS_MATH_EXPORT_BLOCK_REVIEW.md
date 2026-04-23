# Thread B Axis Math Export Block Review

**Date:** 2026-03-29
**Status:** Review-only packet of candidate `EXPORT_BLOCK v1` wrappers for the first axis-math vocabulary set.
**Source:** [THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md)

---

## 1. Coordinate Admission Blocks

The following four lexemes are new to Thread B. They must be admitted before the export blocks that reference them can move beyond review. Each block documents the definition, grounding, and any conditional requirements.

### CA-1: `S3_carrier`

```text
BEGIN COORD_ADMISSION v1
LEXEME: S3_carrier
ADMISSION_TYPE: GEOMETRIC_PRIMITIVE
DEFINITION: Unit 3-sphere S^3 as spinor carrier space of SU(2).
  Points are unit quaternions q=(a,b,c,d), a^2+b^2+c^2+d^2=1.
  Identified with 2-component complex spinor psi=(z1,z2) via z1=a+ib, z2=c+id.
GROUNDING: Used in engine_core as the primary state carrier (psi_L, psi_R).
DEPENDS_ON: none (primitive)
USED_BY: S_MATH_AX3_PATH_CLASS_DEF, S_MATH_AX2_REPRESENTATION_FRAME_DEF
RISK_NOTE: "S3" is ambiguous. Must always appear as "S3_carrier" or "S3 spinor manifold".
STATUS: ADMIT_CONDITIONAL — require "carrier" qualifier throughout
END COORD_ADMISSION
```

### CA-2: `Hopf_fiber`

```text
BEGIN COORD_ADMISSION v1
LEXEME: Hopf_fiber
ADMISSION_TYPE: GEOMETRIC_PRIMITIVE
DEFINITION: S^1 fiber of the Hopf fibration pi: S^3 -> S^2.
  For fixed (eta, chi): gamma_fiber(u) = psi(phi0+u, chi0; eta0).
  Phase-only path; density rho(u) = rho(0) for all u.
GROUNDING: Ax3 INNER criterion: density-stationary iff path is fiber-class.
DEPENDS_ON: S3_carrier
USED_BY: S_MATH_AX3_PATH_CLASS_DEF
RISK_NOTE: Standard differential geometry vocabulary; low inflation risk.
STATUS: ADMIT
END COORD_ADMISSION
```

### CA-3: `Base_lift_loop` → rename to `horizontal_lift_loop`

```text
BEGIN COORD_ADMISSION v1
LEXEME: horizontal_lift_loop
ALIAS: Base_lift_loop (deprecated — replaced by this preferred name)
ADMISSION_TYPE: GEOMETRIC_PRIMITIVE
DEFINITION: Horizontal lift of a base loop in S^2 via connection A=d(phi)+cos(2*eta)*d(chi).
  Lifted path satisfies A(gamma_dot)=0 (horizontality).
  gamma_base(u) = psi(phi0 - cos(2*eta0)*u, chi0+u; eta0).
  Density changes along path: rho(u) != rho(0) in general.
GROUNDING: Ax3 OUTER criterion. Probe-validated: sim_Ax3_density_path.py
  (fiber max deviation 9.9e-16, base min deviation 0.455).
DEPENDS_ON: S3_carrier, Hopf_fiber
USED_BY: S_MATH_AX3_PATH_CLASS_DEF
RISK_NOTE: "horizontal_lift_loop" aligns with standard diff-geo vocabulary.
STATUS: ADMIT — update all references from Base_lift_loop to horizontal_lift_loop
END COORD_ADMISSION
```

### CA-4: `interaction_picture_isomorphism` → simplify to `interaction_picture_equivalence`

```text
BEGIN COORD_ADMISSION v1
LEXEME: interaction_picture_equivalence
ALIAS: interaction_picture_isomorphism (deprecated — isomorphism adds unnecessary category-theory weight)
ADMISSION_TYPE: ALGEBRAIC_INVARIANT
DEFINITION: Physics is frame-independent under conjugation by V_s(u) = exp(-i H_s u).
  Formal assertion: O_I(u) = V_s(u)^† O_S V_s(u) preserves operator algebra structure.
  Used as Ax2 invariant: direct and conjugated frames encode the same physics.
GROUNDING: Ax2 lock in AXIS_3_4_5_6_QIT_MATH.md.
DEPENDS_ON: none (algebraic invariant)
USED_BY: S_MATH_AX2_REPRESENTATION_FRAME_DEF
RISK_NOTE: HIGH inflation risk for "isomorphism". Simplified to equivalence assertion.
STATUS: ADMIT_CONDITIONAL — update export block INVARIANTS field to interaction_picture_equivalence
END COORD_ADMISSION
```

---

### CA Resolution Summary

| Lexeme | Status | Action |
|---|---|---|
| `S3_carrier` | ADMIT_CONDITIONAL | Add "carrier" qualifier requirement |
| `Hopf_fiber` | ADMIT | No changes |
| `Base_lift_loop` | ADMIT_CONDITIONAL | Rename → `horizontal_lift_loop` |
| `interaction_picture_isomorphism` | ADMIT_CONDITIONAL | Rename → `interaction_picture_equivalence` |

---

## 2. Candidate Batch Wrapper

This wrapper should now be read the same way as the cleaned entropy review batch:

1. explicit dependency on lexeme admission
2. thinner object-family placeholders instead of over-committed coordinate payloads
3. no probe or permit-style closure inside the same shared batch

```text
BEGIN EXPORT_BLOCK v1
EXPORT_ID: AXIS_MATH_TERMS_BATCH_0001
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: AXIS_MATH_TERM_BATCH_V1_REVIEW
CONTENT:
SPEC_HYP S_MATH_AX3_PATH_CLASS_DEF
SPEC_KIND S_MATH_AX3_PATH_CLASS_DEF CORR MATH_DEF
REQUIRES S_MATH_AX3_PATH_CLASS_DEF CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_AX3_PATH_CLASS_DEF CORR OBJECT_FAMILY finite_realized_path_class
DEF_FIELD S_MATH_AX3_PATH_CLASS_DEF CORR OPERATIONS path_differentiation
DEF_FIELD S_MATH_AX3_PATH_CLASS_DEF CORR INVARIANTS density_stationarity_on_fiber
DEF_FIELD S_MATH_AX3_PATH_CLASS_DEF CORR DOMAIN realized_path_family
DEF_FIELD S_MATH_AX3_PATH_CLASS_DEF CORR CODOMAIN binary_path_classifier
ASSERT S_MATH_AX3_PATH_CLASS_DEF CORR EXISTS MATH_TOKEN path_class_functional
DEF_FIELD S_MATH_AX3_PATH_CLASS_DEF CORR FORMULA "path_class = (d(rho)/du == 0) ? INNER : OUTER"

SPEC_HYP S_TERM_AX3_LOOP_FAMILY
SPEC_KIND S_TERM_AX3_LOOP_FAMILY CORR TERM_DEF
REQUIRES S_TERM_AX3_LOOP_FAMILY CORR S_MATH_AX3_PATH_CLASS_DEF
DEF_FIELD S_TERM_AX3_LOOP_FAMILY CORR TERM "axis3_path_class"
DEF_FIELD S_TERM_AX3_LOOP_FAMILY CORR BINDS S_MATH_AX3_PATH_CLASS_DEF
ASSERT S_TERM_AX3_LOOP_FAMILY CORR EXISTS TERM_TOKEN axis3_path_class

SPEC_HYP S_MATH_AX5_GENERATOR_CLASS_DEF
SPEC_KIND S_MATH_AX5_GENERATOR_CLASS_DEF CORR MATH_DEF
REQUIRES S_MATH_AX5_GENERATOR_CLASS_DEF CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_AX5_GENERATOR_CLASS_DEF CORR OBJECT_FAMILY finite_generator_class
DEF_FIELD S_MATH_AX5_GENERATOR_CLASS_DEF CORR OPERATIONS commutator_analysis
DEF_FIELD S_MATH_AX5_GENERATOR_CLASS_DEF CORR INVARIANTS entropy_conservation_on_unitary_branch
DEF_FIELD S_MATH_AX5_GENERATOR_CLASS_DEF CORR DOMAIN finite_generator_family
DEF_FIELD S_MATH_AX5_GENERATOR_CLASS_DEF CORR CODOMAIN binary_generator_classifier
ASSERT S_MATH_AX5_GENERATOR_CLASS_DEF CORR EXISTS MATH_TOKEN generator_class_functional
DEF_FIELD S_MATH_AX5_GENERATOR_CLASS_DEF CORR FORMULA "class = (-i[H, rho]) ? COHERENT : DISSIPATIVE"

SPEC_HYP S_TERM_AX5_KERNEL_TYPE
SPEC_KIND S_TERM_AX5_KERNEL_TYPE CORR TERM_DEF
REQUIRES S_TERM_AX5_KERNEL_TYPE CORR S_MATH_AX5_GENERATOR_CLASS_DEF
DEF_FIELD S_TERM_AX5_KERNEL_TYPE CORR TERM "axis5_operator_class"
DEF_FIELD S_TERM_AX5_KERNEL_TYPE CORR BINDS S_MATH_AX5_GENERATOR_CLASS_DEF
ASSERT S_TERM_AX5_KERNEL_TYPE CORR EXISTS TERM_TOKEN axis5_operator_class

SPEC_HYP S_MATH_AX2_REPRESENTATION_FRAME_DEF
SPEC_KIND S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR MATH_DEF
REQUIRES S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR OBJECT_FAMILY finite_frame_rotation
DEF_FIELD S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR OPERATIONS rotating_frame_transformation
DEF_FIELD S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR INVARIANTS interaction_picture_equivalence
DEF_FIELD S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR DOMAIN finite_frame_family
DEF_FIELD S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR CODOMAIN frame_identity_set
ASSERT S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR EXISTS MATH_TOKEN interaction_picture_unitary
DEF_FIELD S_MATH_AX2_REPRESENTATION_FRAME_DEF CORR FORMULA "V(u) = exp(-i H_s u)"

SPEC_HYP S_TERM_AX2_FRAME_ROTATION
SPEC_KIND S_TERM_AX2_FRAME_ROTATION CORR TERM_DEF
REQUIRES S_TERM_AX2_FRAME_ROTATION CORR S_MATH_AX2_REPRESENTATION_FRAME_DEF
DEF_FIELD S_TERM_AX2_FRAME_ROTATION CORR TERM "axis2_frame_class"
DEF_FIELD S_TERM_AX2_FRAME_ROTATION CORR BINDS S_MATH_AX2_REPRESENTATION_FRAME_DEF
ASSERT S_TERM_AX2_FRAME_ROTATION CORR EXISTS TERM_TOKEN axis2_frame_class

SPEC_HYP S_MATH_AX4_LOOP_COMMUTATION_DEF
SPEC_KIND S_MATH_AX4_LOOP_COMMUTATION_DEF CORR MATH_DEF
REQUIRES S_MATH_AX4_LOOP_COMMUTATION_DEF CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_AX4_LOOP_COMMUTATION_DEF CORR OBJECT_FAMILY finite_ordered_channel_family
DEF_FIELD S_MATH_AX4_LOOP_COMMUTATION_DEF CORR OPERATIONS channel_chaining
DEF_FIELD S_MATH_AX4_LOOP_COMMUTATION_DEF CORR INVARIANTS orientation_dependence
DEF_FIELD S_MATH_AX4_LOOP_COMMUTATION_DEF CORR DOMAIN ordered_channel_family
DEF_FIELD S_MATH_AX4_LOOP_COMMUTATION_DEF CORR CODOMAIN loop_ordering_set
ASSERT S_MATH_AX4_LOOP_COMMUTATION_DEF CORR EXISTS MATH_TOKEN loop_commutation_functional
DEF_FIELD S_MATH_AX4_LOOP_COMMUTATION_DEF CORR FORMULA "[U, E] != 0 -> (U o E o U o E) != (E o U o E o U)"

SPEC_HYP S_TERM_AX4_LOOP_ORDER
SPEC_KIND S_TERM_AX4_LOOP_ORDER CORR TERM_DEF
REQUIRES S_TERM_AX4_LOOP_ORDER CORR S_MATH_AX4_LOOP_COMMUTATION_DEF
DEF_FIELD S_TERM_AX4_LOOP_ORDER CORR TERM "axis4_loop_order"
DEF_FIELD S_TERM_AX4_LOOP_ORDER CORR BINDS S_MATH_AX4_LOOP_COMMUTATION_DEF
ASSERT S_TERM_AX4_LOOP_ORDER CORR EXISTS TERM_TOKEN axis4_loop_order
END EXPORT_BLOCK v1
```

---

## 3. Review Notes

| Risk | Status after CA pass |
|---|---|
| lexeme dependency order | RESOLVED at review level — wrapper now depends on the coordinate-admission packet instead of re-declaring concrete coordinate payloads |
| over-specified coordinate payloads | RESOLVED at review level — object-family placeholders replace overly committed wrapper text |
| Ax4 U/E support packet | OPEN — U branch = Ne/Si (Ax1 NU), E branch = Se/Ni (Ax1 U); later Ax1 support packet still pending |
| Ax1 exclusion | OPEN — Ax1 is derived (Ax0 × Ax2); will stay in a later packet after Ax0+Ax2 blocks are cleaner |
| Ax4 probe packet | OPEN — `sim_Ax4_commutation.py` now exists, but the review wrapper still depends on a cleaner Ax1 antecedent handoff before any promotion |

## 4. Batch Submission Order

1. Treat the coordinate-admission packet as the upstream review dependency
2. Keep AX3, AX5, and AX2 at thinner `MATH_DEF + TERM_DEF` review shape
3. Keep `sim_Ax4_commutation.py` as supporting probe evidence rather than reopening the wrapper
4. Keep AX4 in review until the later Ax1 support packet is cleaner and the controller explicitly allows promotion work
