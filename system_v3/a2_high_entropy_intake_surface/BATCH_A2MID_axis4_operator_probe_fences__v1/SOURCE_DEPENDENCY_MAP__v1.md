# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axis4_operator_probe_fences__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_axis4_qit_math_term_conflict__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_axes_master_semantic_fences__v1`
- `BATCH_A2MID_axis_foundation_overlay_fences__v1`
- `BATCH_A2MID_axis12_topology_candidate_fences__v1`
- `BATCH_A2MID_axis4_directional_evidence_isolation__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the parent term-conflict batch as the primary source-bearing artifact
- the Axes Master A2-mid batch is used to keep the later `Axis-4 = variance-order math-class split` rule distinct from the note's stronger definitional claim
- the axis-foundation and axis12 A2-mid batches are used to keep:
  - alias-only topology scope
  - derived-geometry ordering
  - candidate channel-family handling
  separate from the note's harder legacy-stage lock
- the axis4 directional evidence A2-mid batch is used to keep loop-order experiments in the evidence/probe lane rather than letting the note's loop words self-upgrade into theorem
- a fresh raw-source reread was used because the reduction needed exact wording for:
  - `Axis-4 (QIT definition)`
  - `Rosetta only`
  - explicit loop words and invariant checks

## Candidate-to-parent dependency map
- `RC1_QIT_NATIVE_AXIS4_PROBE_FRAMING_RULE`
  - parent cluster:
    - `C1`
  - parent distillates:
    - `D1`
    - `D2`
  - parent candidate:
    - `C1`
    - `C2`
  - parent tension:
    - `T2`
  - comparison anchor:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC2`
- `RC2_OPERATOR_ORDERING_LOOPWORD_AND_INVARIANT_PACKET`
  - parent clusters:
    - `C1`
    - `C5`
  - parent distillates:
    - `D2`
    - `D5`
  - parent candidate:
    - `C1`
    - `C2`
  - parent tensions:
    - `T2`
    - `T5`
  - comparison anchor:
    - `BATCH_A2MID_axis4_directional_evidence_isolation__v1:RC6`
- `RC3_ROSETTA_HUMAN_VERIFICATION_ONLY_RULE`
  - parent cluster:
    - `C3`
  - parent distillate:
    - `D3`
  - parent tensions:
    - `T3`
    - `T4`
- `RC4_EXPLICIT_QUBIT_CHANNEL_MENU_AS_CANDIDATE_STAGE_FUEL`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D3`
  - parent tensions:
    - `T3`
    - `T7`
  - comparison anchor:
    - `BATCH_A2MID_axis12_topology_candidate_fences__v1:RC2`

## Quarantine dependency map
- `Q1_AXIS4_EQUALS_UNITARY_NONUNITARY_ORDERING_DEFINITION`
  - parent tension:
    - `T2`
  - parent candidate:
    - `C3`
- `Q2_FIXED_LEGACY_LABEL_AND_TERRAIN_STAGE_LOCK`
  - parent tension:
    - `T3`
  - parent candidate:
    - `C3`
- `Q3_AXIS5_AS_DRIVE_ACTIVATION_AMPLITUDE_OVERLAY`
  - parent distillate:
    - `D4`
  - parent tension:
    - `T4`
  - parent candidate:
    - `C3`
- `Q4_EXACTLY_ONE_MINIMAL_CLOSED_CYCLE_AS_SETTLED_THEOREM`
  - parent tension:
    - `T5`
  - parent candidate:
    - `C3`
- `Q5_STITCHED_TOPOLOGY_AND_STAGE_IDENTITY_COLLAPSE`
  - parent tension:
    - `T6`
    - `T7`
  - parent candidate:
    - `C5`
