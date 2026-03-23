# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_geometry_manifold_axis_fences__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_canon_geometry_manifold_term_conflict__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_axes_master_semantic_fences__v1`
- `BATCH_A2MID_axis_foundation_overlay_fences__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the canon-geometry term-conflict parent batch as the primary source-bearing artifact
- the Axes Master and Axis Foundation Companion A2-mid batches are used only as comparison anchors so already-compressed neighboring fence packets do not get recopied wholesale
- no fresh raw-doc reread was needed because the parent batch already isolates:
  - manifold-before-axes rule
  - admissibility-first coordinate-free geometry
  - axes-as-slices formalization
  - Axis-3 engine-family-only narrowing
  - engines-as-derived placement
  - executable compliance checklist

## Candidate-to-parent dependency map
- `RC1_CONSTRAINT_MANIFOLD_BEFORE_AXES_FOUNDATION_PACKET`
  - parent clusters:
    - `C1`
    - `C2`
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T2`
    - `T3`
  - comparison anchor:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC1`
- `RC2_ADMISSIBILITY_FIRST_COORDINATE_FREE_GEOMETRY_RULE`
  - parent cluster:
    - `C2`
  - parent distillate:
    - `D1`
  - parent tension:
    - `T2`
- `RC3_AXES_AS_SLICES_NONCARRIER_RULE`
  - parent cluster:
    - `C3`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T3`
  - comparison anchor:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC1`
- `RC4_AXIS3_ENGINE_FAMILY_ONLY_FENCE`
  - parent clusters:
    - `C4`
    - `C5`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T4`
    - `T6`
  - comparison anchors:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC3`
    - `BATCH_A2MID_axis_foundation_overlay_fences__v1:Q2`
- `RC5_ENGINES_AS_DERIVED_EQUIVALENCE_CLASS_RULE`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D4`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T3`
- `RC6_COMPLIANCE_CHECKLIST_REVIEW_GATE`
  - parent cluster:
    - `C5`
  - parent distillates:
    - `D5`
    - `D6`
  - parent candidates:
    - `C1`
    - `C4`
  - parent tensions:
    - `T1`
    - `T4`

## Quarantine dependency map
- `Q1_AUTHORITY_LABEL_DIRECT_PROMOTION`
  - parent tension:
    - `T1`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C3`
- `Q2_ABSTRACT_MANIFOLD_FOUNDATION_AS_SUFFICIENT_SIM_SUBSTRATE`
  - parent tension:
    - `T2`
- `Q3_AXIS3_FLUX_CHIRALITY_COMPATIBILITY_READ`
  - parent tension:
    - `T4`
  - parent distillate:
    - `D3`
  - comparison anchor:
    - `BATCH_A2MID_axis_foundation_overlay_fences__v1:Q2`
- `Q4_TYPE1_TYPE2_EXTRA_SEMANTICS_REIMPORT`
  - parent tension:
    - `T6`
- `Q5_DERIVED_GEOMETRY_OR_SUBSTRATE_IMPORT_FROM_MINIMAL_FENCE`
  - parent tensions:
    - `T2`
    - `T5`
  - parent candidate:
    - `C3`
