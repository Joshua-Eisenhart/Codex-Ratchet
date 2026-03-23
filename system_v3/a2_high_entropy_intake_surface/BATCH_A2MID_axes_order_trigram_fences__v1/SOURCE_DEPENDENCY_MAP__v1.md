# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_axes_order_trigram_fences__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_axes_order_trigrams_term_conflict__v1`

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
- this pass operates from the parent term-conflict batch as the primary source-bearing artifact
- the Axes Master A2-mid batch is used only as a comparison anchor so partial order-lineage alignment can be separated from the note's older direct axis semantics
- a fresh raw-source reread was used because the reduction needed exact source wording for:
  - `correct global axis order`
  - the `6-5-3` versus `4-1-2` trigram split
  - the note's own diagnosis of earlier conflation

## Candidate-to-parent dependency map
- `RC1_BUILD_ORDER_LINEAGE_WITHOUT_ONTOLOGY_PRECEDENCE`
  - parent cluster:
    - `C1`
  - parent distillate:
    - `D1`
  - parent candidate:
    - `C1`
  - parent tensions:
    - `T1`
    - `T2`
  - comparison anchor:
    - `BATCH_A2MID_axes_master_semantic_fences__v1:RC6`
- `RC2_ENGINE_STAGE_TRIGRAM_SCAFFOLD_PACKET`
  - parent clusters:
    - `C2`
    - `C3`
  - parent distillate:
    - `D2`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T2`
    - `T6`
- `RC3_SELF_DIAGNOSED_CONFLATION_WITNESS_PACKET`
  - parent distillate:
    - `D5`
  - parent tensions:
    - `T5`
    - `T6`
    - `T7`
- `RC4_NONCANON_ROSETTA_FUEL_ONLY_RULE`
  - parent distillate:
    - `D6`
  - parent candidate:
    - `C4`
    - `C5`
  - parent tensions:
    - `T1`
    - `T7`

## Quarantine dependency map
- `Q1_AXIS0_AS_EXISTENCE_ENTROPY_GRADIENT_NONCOMMUTATION`
  - parent distillate:
    - `D3`
  - parent tension:
    - `T3`
  - parent candidate:
    - `C3`
- `Q2_AXIS5_AS_DRIVE_ACTIVATION_AMPLITUDE`
  - parent distillate:
    - `D3`
  - parent tension:
    - `T4`
  - parent candidate:
    - `C3`
- `Q3_AXIS3_AS_FLUX_CHIRALITY_ENGINE_ESSENCE`
  - parent distillate:
    - `D3`
  - parent tension:
    - `T5`
  - parent candidate:
    - `C3`
- `Q4_STAGE_TRIGRAM_AS_CURRENT_EIGHT_STAGE_LAW`
  - parent distillate:
    - `D4`
  - parent tension:
    - `T6`
  - parent candidate:
    - `C3`
- `Q5_CORRECT_GLOBAL_AXIS_ORDER_AS_SELF_AUTHORIZED_CANON`
  - parent cluster:
    - `C6`
  - parent tension:
    - `T1`
    - `T2`
  - parent candidate:
    - `C4`
