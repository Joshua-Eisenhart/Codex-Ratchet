# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_physics_fuel_quarantine_gates__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_physics_fuel_digest_term_conflict__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_geometry_manifold_axis_fences__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the physics-fuel digest term-conflict batch as the primary source-bearing artifact
- the geometry/manifold A2-mid batch is used only as a comparison anchor so the digest's derived-geometry sequencing is not detached from nearby fence context
- no fresh raw-doc reread was needed because the parent batch already isolates:
  - overlay-only noncontamination contract
  - candidate primitive inventory
  - rewrite requirement
  - operator-only salvage phrasing
  - non-time / non-signal boundary
  - staged admission order

## Candidate-to-parent dependency map
- `RC1_PHYSICS_FUEL_NONCONTAMINATION_CONTRACT`
  - parent cluster:
    - `C1`
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tensions:
    - `T1`
    - `T6`
- `RC2_CANDIDATE_TERM_MENU_WITHOUT_ENDORSEMENT_RULE`
  - parent cluster:
    - `C2`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C1`
  - parent tensions:
    - `T1`
    - `T5`
    - `T7`
- `RC3_OPERATOR_TESTABLE_REWRITE_GATE`
  - parent cluster:
    - `C3`
  - parent distillates:
    - `D1`
    - `D6`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T6`
- `RC4_RETROCAUSAL_BOUNDARY_VALUE_OPERATOR_SALVAGE`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T2`
    - `T3`
- `RC5_NO_PRIMITIVE_TIME_CAUSALITY_PRIVILEGED_FUTURE_FENCE`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D3`
  - parent tension:
    - `T3`
- `RC6_OPERATOR_TO_DERIVED_GEOMETRY_TO_KILLABLE_GRAVITY_ORDER`
  - parent clusters:
    - `C5`
    - `C2`
  - parent distillate:
    - `D4`
  - parent candidates:
    - `C2`
    - `C4`
  - parent tensions:
    - `T4`
    - `T7`
  - comparison anchor:
    - `BATCH_A2MID_geometry_manifold_axis_fences__v1:RC1`
    - `BATCH_A2MID_geometry_manifold_axis_fences__v1:RC2`

## Quarantine dependency map
- `Q1_METAPHYSICAL_NARRATIVE_BUNDLE`
  - parent cluster:
    - `C3`
  - parent candidate:
    - `C3`
  - parent tension:
    - `T2`
- `Q2_BERRY_CHIRALITY_HOPF_WIGNER_STYLE_TERMS_AS_ALREADY_LICENSED_KERNEL`
  - parent cluster:
    - `C2`
  - parent candidate:
    - `C3`
  - parent tensions:
    - `T4`
    - `T5`
- `Q3_PATH_INTEGRAL_BOUNDARY_VALUE_LANGUAGE_AS_PRIVILEGED_FUTURE_REOPENING`
  - parent cluster:
    - `C4`
  - parent tension:
    - `T3`
- `Q4_GRAVITY_AS_GRADIENT_AS_ENDORSED_MODEL_CONTENT`
  - parent cluster:
    - `C2`
    - `C5`
  - parent candidate:
    - `C3`
  - parent tension:
    - `T7`
- `Q5_REPO_REUSE_AS_CANONIZATION`
  - parent distillate:
    - `D5`
  - parent candidate:
    - `C4`
