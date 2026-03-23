# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis4_axis5_direction_intensity_fences__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_axis4_vs_axis5_heat_cold_term_conflict__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_axes_master_semantic_fences__v1`
- `BATCH_A2MID_axis_foundation_overlay_fences__v1`
- `BATCH_A2MID_axis4_operator_probe_fences__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the parent term-conflict batch as the primary source-bearing artifact
- the Axes Master A2-mid batch is used to keep the later `Axis-4` / `Axis-5` semantic packet distinct from this older thermodynamic correction note
- the axis-foundation A2-mid batch is used to keep:
  - `Axis-4 is not loop order`
  - overlay/nonreplacement discipline
  separate from the note's stronger direction lock
- the axis4 operator-probe A2-mid batch is used to keep loop-direction language in the probe and comparison lane rather than letting this note's correction self-upgrade into current axis definition
- a fresh raw-source reread was used because the reduction depends on exact correction wording around:
  - one cycle
  - two traversal directions
  - `hot/cold` as state or reservoir property rather than direction
  - same-cycle direction change versus same-direction intensity change

## Candidate-to-parent dependency map
- `RC1_ONE_LOOP_TWO_TRAVERSAL_DIRECTIONS_CORRECTION_RULE`
  - parent cluster:
    - `C1`
  - parent distillates:
    - `D1`
    - `D3`
  - parent candidates:
    - `C1`
    - `C4`
  - parent tensions:
    - `T4`
    - `T5`
- `RC2_DIRECTION_VERSUS_INTENSITY_SEPARATION_PACKET`
  - parent cluster:
    - `C2`
  - parent distillates:
    - `D2`
    - `D5`
  - parent candidates:
    - `C2`
    - `C4`
  - parent tensions:
    - `T2`
    - `T3`
  - comparison anchors:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC2`
    - `BATCH_A2MID_axis_foundation_overlay_fences__v1:RC2`
- `RC3_THERMO_ANALOGY_COMPARATIVE_CHECK_ONLY_RULE`
  - parent clusters:
    - `C1`
    - `C3`
  - parent distillates:
    - `D1`
    - `D6`
  - parent tensions:
    - `T1`
    - `T4`
  - comparison anchor:
    - `BATCH_A2MID_axis4_operator_probe_fences__v1:RC1`
- `RC4_SAME_CYCLE_DIRECTION_CHANGE_VS_SAME_DIRECTION_INTENSITY_PACKET`
  - parent cluster:
    - `C3`
  - parent distillates:
    - `D2`
    - `D5`
    - `D6`
  - parent candidates:
    - `C2`
    - `C4`
  - parent tensions:
    - `T2`
    - `T3`
    - `T5`
  - comparison anchor:
    - `BATCH_A2MID_axis4_operator_probe_fences__v1:RC2`

## Quarantine dependency map
- `Q1_AXIS4_EQUALS_HEATING_COOLING_DIRECTION_DEFINITION`
  - `TENSION_MAP__v1.md:T2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q2_AXIS5_INTENSITY_PACKET_AS_SETTLED_CURRENT_CANON`
  - `A2_3_DISTILLATES__v1.md:D5`
  - `TENSION_MAP__v1.md:T3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q3_CARNOT_ANALOGY_AS_GOVERNING_AXIS_SEMANTIC_BASIS`
  - `TENSION_MAP__v1.md:T4`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q4_INDUCTIVE_DEDUCTIVE_EQUALS_ENGINE_REFRIGERATOR_DIRECTION_LOCK`
  - `CLUSTER_MAP__v1.md:C2`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C3`
- `Q5_FINAL_LOCK_SELF_AUTHORIZATION`
  - `CLUSTER_MAP__v1.md:C3`
  - `TENSION_MAP__v1.md:T1`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md:C5`
