# Thread B Lexeme Coordinate Admission Candidates

**Date:** 2026-03-29
**Status:** DRAFT lexeme admission blocks for the undeclared terms in both the Entropy and Axis-Math export batches. These must be admitted BEFORE the export wrappers can be treated as safe.

---

## 1. Scope

The Stack Audit (Warning 1) identified the following undeclared or unstable lexeme families used in export wrappers:

**From Entropy Batch:**
- `density_matrix`
- `bipartite_density_matrix`
- `finite_scalar_encoding`
- `basis_invariant`
- `signed_cut_functional`
- `coherent_information_relation`

**From Axis-Math Batch:**
- `S3_carrier`
- `Hopf_fiber`
- `horizontal_lift_loop`
- `density_derivative`
- `CPTP_channel`
- `Lindblad_generator`
- `Unitary_commutator`
- `Weyl_sheet`
- `Interaction_unitary`
- `Rotating_frame`
- `interaction_picture_equivalence`
- `CPTP_semigroup`
- `Channel_composition`
- `non_commutativity`

---

## 2. Candidate Lexeme Blocks

### Tier 1: Root-Earned (F01 + N01 direct consequences)

These lexemes are direct consequences of the root constraints and can be admitted first.

```text
LEXEME_DEF finite_carrier
  SOURCE: F01_FINITUDE
  MEANING: any carrier space with finite dimension
  STATUS: ROOT_EARNED

LEXEME_DEF noncommutative_composition
  SOURCE: N01_NONCOMMUTATION
  MEANING: order-sensitive application of maps
  STATUS: ROOT_EARNED

LEXEME_DEF non_commutativity
  SOURCE: N01_NONCOMMUTATION
  MEANING: property that composition order matters
  REQUIRES: noncommutative_composition
  STATUS: ROOT_EARNED

LEXEME_DEF finite_scalar_encoding
  SOURCE: F01_FINITUDE
  MEANING: scalar output of a functional on a finite carrier
  STATUS: ROOT_EARNED
```

### Tier 2: Admitted Math (QIT Basin)

These lexemes come from the admitted finite-QIT working basin.

```text
LEXEME_DEF density_matrix
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: positive semidefinite trace-1 operator on finite Hilbert space
  REQUIRES: finite_carrier
  STATUS: MATH_BASIN_ADMITTED

LEXEME_DEF bipartite_density_matrix
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: density_matrix on tensor product H_A x H_B
  REQUIRES: density_matrix
  STATUS: MATH_BASIN_ADMITTED

LEXEME_DEF CPTP_channel
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: completely positive trace-preserving map on density matrices
  REQUIRES: density_matrix
  STATUS: MATH_BASIN_ADMITTED
  NOTE: math object (the map); distinct from proper_cptp_branch (branch classification in TERM_ADMISSION_MAP)

LEXEME_DEF Lindblad_generator
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: generator of CPTP semigroup in GKLS form
  REQUIRES: CPTP_channel
  STATUS: MATH_BASIN_ADMITTED

LEXEME_DEF Unitary_commutator
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: commutator generator -i[H, rho] of unitary evolution
  REQUIRES: density_matrix
  STATUS: MATH_BASIN_ADMITTED
  NOTE: generator form only; does not elevate unitary_branch (branch classification) to canonical status

LEXEME_DEF CPTP_semigroup
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: one-parameter family of CPTP maps with composition
  REQUIRES: CPTP_channel noncommutative_composition
  STATUS: MATH_BASIN_ADMITTED

LEXEME_DEF Channel_composition
  SOURCE: ADMITTED_QIT_BASIN + N01_NONCOMMUTATION
  MEANING: ordered application of CPTP maps
  REQUIRES: CPTP_channel noncommutative_composition
  STATUS: MATH_BASIN_ADMITTED

```
<!-- non_commutativity moved to Tier 1 block (ROOT_EARNED, not MATH_BASIN_ADMITTED); duplicate removed 2026-03-29 -->

### Tier 3: Favored Geometry (Hopf/Weyl Realization)

These lexemes are downstream of the favored geometry realization. They are NOT root-earned.

```text
LEXEME_DEF S3_carrier
  SOURCE: FAVORED_GEOMETRY_BASIN
  MEANING: unit 3-sphere in C^2 as spinor carrier
  REQUIRES: finite_carrier
  STATUS: REALIZATION_ADMITTED
  FENCE: favored realization, not root consequence

LEXEME_DEF Hopf_fiber
  SOURCE: FAVORED_GEOMETRY_BASIN
  MEANING: S^1 fiber of the Hopf projection S^3 -> S^2
  REQUIRES: S3_carrier
  STATUS: REALIZATION_ADMITTED
  FENCE: geometry-specific, not universal

LEXEME_DEF horizontal_lift_loop
  SOURCE: FAVORED_GEOMETRY_BASIN
  MEANING: horizontal connection-lifted loop on S^3
  REQUIRES: S3_carrier Hopf_fiber
  STATUS: REALIZATION_ADMITTED

LEXEME_DEF Weyl_sheet
  SOURCE: FAVORED_GEOMETRY_BASIN
  MEANING: left or right Weyl spinor component
  REQUIRES: S3_carrier
  STATUS: REALIZATION_ADMITTED

LEXEME_DEF Interaction_unitary
  SOURCE: FAVORED_GEOMETRY_BASIN + ADMITTED_QIT_BASIN
  MEANING: V(u) = exp(-i H_s u) frame rotation unitary
  REQUIRES: Weyl_sheet Unitary_commutator
  STATUS: REALIZATION_ADMITTED

LEXEME_DEF interaction_picture_equivalence
  SOURCE: FAVORED_GEOMETRY_BASIN + ADMITTED_QIT_BASIN
  MEANING: frame-change equivalence preserving the same physics under interaction-picture conjugation
  REQUIRES: Interaction_unitary
  STATUS: REALIZATION_ADMITTED
  FENCE: equivalence read only; avoid extra category-theory weight

LEXEME_DEF Rotating_frame
  SOURCE: FAVORED_GEOMETRY_BASIN
  MEANING: interaction picture induced by Weyl sheet Hamiltonian
  REQUIRES: Interaction_unitary interaction_picture_equivalence
  STATUS: REALIZATION_ADMITTED
```

### Tier 4: Entropy-Functional (Late-Derived)

```text
LEXEME_DEF basis_invariant
  SOURCE: ADMITTED_QIT_BASIN
  MEANING: property of a functional that is independent of basis choice
  REQUIRES: density_matrix
  STATUS: MATH_BASIN_ADMITTED

LEXEME_DEF signed_cut_functional
  SOURCE: ENTROPY_BRANCH
  MEANING: functional on bipartite density matrix that can take negative values
  REQUIRES: bipartite_density_matrix
  STATUS: LEXEME_ADMITTED_WITH_FENCE
  FENCE: cut-dependent, needs bridge/cut resolution

LEXEME_DEF coherent_information_relation
  SOURCE: ENTROPY_BRANCH
  MEANING: I_c(A>B) = -S(A|B) identity relating coherent information to conditional entropy
  REQUIRES: signed_cut_functional
  STATUS: LEXEME_ADMITTED_WITH_FENCE
  FENCE: downstream of cut doctrine

LEXEME_DEF density_derivative
  SOURCE: FAVORED_GEOMETRY_BASIN
  MEANING: d(rho)/du along a parameterized path on the carrier
  REQUIRES: density_matrix S3_carrier
  STATUS: REALIZATION_ADMITTED
```

---

## 3. Admission Order

The safe admission order respects the constraint chain:

1. **Root-earned** → `finite_carrier`, `noncommutative_composition`, `finite_scalar_encoding`, `non_commutativity`
2. **QIT Basin** → `density_matrix`, `bipartite_density_matrix`, `CPTP_channel`, etc.
3. **Geometry Realization** → `S3_carrier`, `Hopf_fiber`, `horizontal_lift_loop`, `Weyl_sheet`, `interaction_picture_equivalence`, etc.
4. **Entropy Functionals** → `basis_invariant`, `signed_cut_functional`, etc.

---

## 4. What This Clears

If this lexeme batch is accepted as review-ready, it unblocks:

- **Entropy Export Batch** (`ENTROPY_TERMS_BATCH_0001`): all object-level lexemes are now declared
- **Axis-Math Export Batch** (`AXIS_MATH_TERMS_BATCH_0001`): all geometry and operator lexemes are declared
- **Review-safe cleanup**: later staging wrappers can now refer to typed lexemes instead of undefined literals

---

## 5. Do Not Smooth

- Do not treat lexeme admission as term admission. Lexemes are vocabulary; terms are bound math.
- Do not let Tier 3 (geometry) lexemes appear at the same admission level as Tier 1 (root).
- Do not let the lexeme list become an ontology claim. It is a vocabulary registry.
