# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis_foundation_overlay_fences__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_axis_foundation_companion_term_conflict__v1`

## Comparison anchor used for narrowing
- `BATCH_A2MID_axes_master_semantic_fences__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the companion term-conflict parent batch as the primary source-bearing artifact
- the Axes Master A2-mid batch is used only as a comparison anchor so aligned fences can be separated from new overlay pressure
- no fresh raw-doc reread was needed because the parent batch already isolates:
  - overlay-only nonreplacement contract
  - drift hazards and naming locks
  - Topology4 math-first anchors
  - derived-geometry placement
  - operator-role rosetta mapping
  - direct Axis-3 and Terrain8 conflict zones

## Candidate-to-parent dependency map
- `RC1_OVERLAY_NONREPLACEMENT_VERIFICATION_CONTRACT`
  - parent cluster:
    - `C1`
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tensions:
    - `T1`
    - `T2`
- `RC2_DRIFT_HAZARD_AND_NAMING_LOCK_PACKET`
  - parent cluster:
    - `C2`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T2`
    - `T4`
- `RC3_TOPOLOGY4_MATH_FIRST_ALIAS_DEMOTION_PACKET`
  - parent cluster:
    - `C3`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T1`
    - `T5`
  - comparison anchor:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC4`
- `RC4_DERIVED_GEOMETRY_AFTER_KERNEL_OBJECTS_RULE`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D4`
  - parent tension:
    - `T6`
- `RC5_OPERATOR_ROLE_ROSETTA_WITH_AXIS6_VARIANT_BOUNDARY`
  - parent cluster:
    - `C5`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T4`
    - `T7`
- `RC6_SIMS_DECIDE_MAPPING_OVERLAY_STAYS_PROVISIONAL_RULE`
  - parent cluster:
    - `C6`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C1`
    - `C5`
  - parent tensions:
    - `T5`
    - `T7`

## Quarantine dependency map
- `Q1_OVERLAY_GUIDANCE_AS_SELF_AUTHORIZED_KERNEL_SETTLEMENT`
  - parent tensions:
    - `T1`
    - `T2`
  - parent candidate:
    - `C1`
- `Q2_AXIS3_AS_FLUX2_COMPATIBLE_WITH_CANON`
  - parent tension:
    - `T3`
  - parent distillate:
    - `D5`
  - parent candidate:
    - `C3`
- `Q3_TERRAIN8_STAGE8_AS_KERNEL_AXIS_ESSENCE`
  - parent tension:
    - `T5`
  - parent candidate:
    - `C3`
- `Q4_DERIVED_GEOMETRY_AS_DIRECT_KERNEL_MEANING`
  - parent tension:
    - `T6`
  - parent distillate:
    - `D4`
- `Q5_JUNG_IGT_OPERATOR_ROLES_AS_KERNEL_ONTOLOGY`
  - parent tension:
    - `T7`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C3`
