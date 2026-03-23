# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_v02_bridge_ordering__v1`
Extraction mode: `QIT_BRIDGE_REDUCTION_PASS`
Date: 2026-03-08

## Primary parent batch
- `BATCH_refinedfuel_axis0_spec_options_v02_qit_bridge__v1`

## Comparison anchor used for narrowing
- `BATCH_A2MID_axis0_option_menu_adjudication__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the v0.2 parent batch as the primary source-bearing artifact
- the v0.1 A2-mid batch is used only as a comparison anchor so repeated option-menu material does not get recopied into another large packet
- no fresh raw-doc reread was needed because the parent batch already isolates:
  - draft-vs-admission posture
  - monotone clock criterion
  - nested-factorization shell bookkeeping
  - four-family menu and finite-step gradients
  - `jk fuzz` to Kraus / Stinespring bridge
  - sim contact and geometry-last ratchet order

## Candidate-to-parent dependency map
- `RC1_DRAFT_QUARANTINE_WITH_ADMISSION_PREP_PATTERN`
  - parent cluster:
    - `C1`
    - `C2`
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tensions:
    - `T1`
    - `T4`
- `RC2_NONMETAPHYSICAL_MONOTONE_I_SCALAR_CONTRACT`
  - parent cluster:
    - `C2`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T3`
- `RC3_SHELL_TO_NESTED_FACTORIZATION_BASELINE`
  - parent cluster:
    - `C3`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T2`
- `RC4_INHERITED_FOUR_FAMILY_MENU_WITH_FINITE_STEP_GRADIENTS`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D4`
  - parent candidate:
    - `C2`
  - comparison anchor:
    - `BATCH_A2MID_axis0_option_menu_adjudication__v1:RC3`
    - `BATCH_A2MID_axis0_option_menu_adjudication__v1:RC4`
- `RC5_BOUNDED_JK_FUZZ_TO_KRAUS_ENVIRONMENT_ROUTE`
  - parent cluster:
    - `C5`
  - parent distillate:
    - `D5`
  - parent tension:
    - `T5`
- `RC6_SIM_CONTACT_WITH_GEOMETRY_LAST_RATCHET_ORDER`
  - parent cluster:
    - `C5`
    - `C6`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C1`
    - `C5`
  - parent tensions:
    - `T6`
    - `T7`

## Quarantine dependency map
- `Q1_SOURCE_LOCAL_TERM_SELF_ADMISSION`
  - parent tension:
    - `T4`
  - parent candidate:
    - `C3`
- `Q2_UNIVERSAL_CLOCK_AS_PRIMITIVE_TIME`
  - parent tension:
    - `T3`
  - parent distillate:
    - `D2`
- `Q3_KRAUS_STINESPRING_STACK_AS_ALREADY_LICENSED_SUBSTRATE`
  - parent tension:
    - `T5`
  - parent candidate:
    - `C3`
- `Q4_HOLOGRAPHIC_OR_CODE_SUBSPACE_REIMPORT`
  - parent tension:
    - `T2`
    - `T7`
  - parent candidate:
    - `C3`
- `Q5_SIM_ALIGNMENT_AS_LOCKED_AXIS0_WINNER`
  - parent tension:
    - `T6`
  - comparison anchor:
    - `BATCH_A2MID_axis0_option_menu_adjudication__v1:RC5`
