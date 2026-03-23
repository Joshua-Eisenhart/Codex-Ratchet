# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis0_v03_measurement_checkpoint__v1`
Extraction mode: `QIT_BRIDGE_REDUCTION_PASS`
Date: 2026-03-08

## Primary parent batch
- `BATCH_refinedfuel_axis0_spec_options_v03_qit_bridge__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_axis0_option_menu_adjudication__v1`
- `BATCH_A2MID_axis0_v02_bridge_ordering__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the v0.3 parent batch as the primary source-bearing artifact
- the v0.1 and v0.2 A2-mid batches are used only as comparison anchors so the reduction can isolate the v0.3 cleanup delta rather than rebuild the older menu and bridge scaffolding
- no fresh raw-doc reread was needed because the parent batch already isolates:
  - canon-anchor plus proposal-only guard
  - minimal perturbation-response setup
  - pairwise spread and variance-control options
  - total-correlation fallback
  - path-entropy and global-order-parameter route
  - explicit nondecision wall

## Candidate-to-parent dependency map
- `RC1_SEMANTIC_ANCHOR_WITH_PROPOSAL_ONLY_MATH_BOUNDARY`
  - parent cluster:
    - `C1`
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tension:
    - `T1`
  - comparison anchors:
    - `BATCH_A2MID_axis0_option_menu_adjudication__v1:RC1`
    - `BATCH_A2MID_axis0_v02_bridge_ordering__v1:RC1`
- `RC2_MINIMAL_PERTURBATION_RESPONSE_MEASUREMENT_SETUP`
  - parent cluster:
    - `C2`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C1`
  - parent tension:
    - `T2`
- `RC3_PAIRWISE_SPREAD_EFFECTIVE_LINK_COUNT_KERNEL`
  - parent cluster:
    - `C3`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C2`
  - parent tension:
    - `T2`
- `RC4_V03_OPTION_REDIRECTION_WITH_GLOBAL_FALLBACK_BOUNDARY`
  - parent clusters:
    - `C3`
    - `C4`
  - parent distillate:
    - `D4`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T3`
    - `T4`
  - comparison anchors:
    - `BATCH_A2MID_axis0_option_menu_adjudication__v1:RC3`
    - `BATCH_A2MID_axis0_option_menu_adjudication__v1:RC4`
    - `BATCH_A2MID_axis0_v02_bridge_ordering__v1:RC4`
- `RC5_PATH_ENTROPY_AND_GLOBAL_ORDER_PARAMETER_NON_TIME_ROUTE`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D5`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T5`
    - `T6`
  - comparison anchors:
    - `BATCH_A2MID_axis0_v02_bridge_ordering__v1:RC2`
    - `BATCH_A2MID_axis0_v02_bridge_ordering__v1:RC5`
- `RC6_EXPLICIT_NONDECISION_AND_NONREPLACEMENT_WALL`
  - parent clusters:
    - `C5`
    - `C6`
  - parent distillate:
    - `D6`
  - parent candidates:
    - `C1`
    - `C4`
  - parent tensions:
    - `T7`
    - `T8`
  - comparison anchors:
    - `BATCH_A2MID_axis0_v02_bridge_ordering__v1:RC3`
    - `BATCH_A2MID_axis0_v02_bridge_ordering__v1:RC6`

## Quarantine dependency map
- `Q1_CANON_ANCHOR_AS_FULL_FILE_RATIFICATION`
  - parent tension:
    - `T1`
  - parent candidate:
    - `C3`
- `Q2_TOTAL_CORRELATION_AS_PERFECT_AXIS0_SEMANTIC_MATCH`
  - parent tension:
    - `T3`
  - parent distillate:
    - `D4`
- `Q3_PATH_ENTROPY_OR_G_SCALAR_AS_PRIMITIVE_TIME_FINAL_INVARIANT`
  - parent tensions:
    - `T5`
    - `T6`
  - parent candidate:
    - `C3`
- `Q4_V03_AS_TOTAL_REPLACEMENT_FOR_V02_BRIDGE_SCAFFOLDING`
  - parent tension:
    - `T7`
  - parent candidate:
    - `C4`
- `Q5_COMPACT_MENU_AS_SETTLED_AXIS0_WINNER`
  - parent candidate:
    - `C3`
  - parent tension:
    - `T8`
