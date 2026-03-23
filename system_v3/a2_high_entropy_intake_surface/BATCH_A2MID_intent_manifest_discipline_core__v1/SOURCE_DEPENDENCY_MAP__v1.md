# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_intent_manifest_discipline_core__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_archived_state_intent_manifest_v1__v1`

## Comparison anchor used for narrowing
- `BATCH_A2MID_episode01_persistence_transition__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the archived intent-manifest intake batch as the primary source-bearing artifact
- the Episode 01 A2-mid batch is used only as a comparison anchor so the manifest's compact posture is not mistaken for the whole archived runtime-state history
- no fresh raw-doc reread was needed because the parent batch already isolates:
  - validator-not-proof-engine framing
  - anti-smoothing and declared-mode discipline
  - A2 preservation/boundary role
  - append-only and lean-memory rules
  - raw-context retention tension
  - archived/non-active status

## Candidate-to-parent dependency map
- `RC1_ARCHIVED_INTENT_PLAQUE_NONAUTHORITY_RULE`
  - parent cluster:
    - `C5`
  - parent distillates:
    - `D1`
    - `D5`
  - parent candidates:
    - `C1`
    - `C5`
- `RC2_CONSTRAINT_FIRST_VALIDATOR_NOT_PROOF_ENGINE_POSITION`
  - parent cluster:
    - `C1`
  - parent distillate:
    - `D1`
  - parent tension:
    - `T4`
- `RC3_DECLARED_MODE_ANTI_SMOOTHING_EXPLICITNESS_PACKET`
  - parent clusters:
    - `C2`
    - `C3`
  - parent distillates:
    - `D2`
    - `D4`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T1`
    - `T3`
- `RC4_A2_PRESERVATION_BOUNDARY_ROLE_PACKET`
  - parent cluster:
    - `C3`
  - parent distillate:
    - `D4`
  - parent candidate:
    - `C2`
- `RC5_APPEND_ONLY_LEAN_MEMORY_DISCIPLINE_PACKET`
  - parent cluster:
    - `C4`
  - parent distillate:
    - `D3`
  - parent candidate:
    - `C2`
  - parent tensions:
    - `T2`
    - `T5`
- `RC6_COMPACT_INTENT_REQUIRES_THICKER_CONTEXT_RULE`
  - parent cluster:
    - `C5`
  - parent distillates:
    - `D1`
    - `D5`
  - parent candidates:
    - `C3`
    - `C5`
  - comparison anchors:
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC1`
    - `BATCH_A2MID_episode01_persistence_transition__v1:RC3`

## Quarantine dependency map
- `Q1_COMPACTNESS_AS_AUTHORITY`
  - parent cluster:
    - `C5`
  - parent distillate:
    - `D5`
  - parent candidate:
    - `C4`
- `Q2_SIMS_ARE_FRUIT_AS_SETTLED_CURRENT_EVIDENCE_DOCTRINE`
  - parent cluster:
    - `C1`
  - parent tension:
    - `T4`
  - parent candidate:
    - `C4`
- `Q3_NO_PARALLEL_BRAINS_AS_CURRENT_ORCHESTRATION_LAW`
  - parent cluster:
    - `C4`
  - parent tension:
    - `T5`
  - parent candidate:
    - `C4`
- `Q4_LOW_VERBOSITY_PLUS_DENSE_NONCOMPRESSED_AS_RESOLVED_STYLE_FORMULA`
  - parent cluster:
    - `C2`
  - parent tension:
    - `T1`
- `Q5_STRUCTURED_EXTRACTION_ONLY_AS_SUFFICIENT_PATH_DEPENDENCE_PRESERVATION`
  - parent clusters:
    - `C3`
    - `C4`
  - parent tension:
    - `T3`
