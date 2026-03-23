# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE-LINKED REDUCTION MAP
Batch: `BATCH_A2MID_sims_axis0_traj_corr_suite_v2_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## 1) Reduction Scope
This A2-mid batch narrows one existing sims orphan intake batch into controller-usable provenance, storage-contract, lattice-visibility, and anti-collapse fences.

Reduction rule used here:
- no raw-source reread
- no runtime execution
- no active A2 append-save
- no contradiction smoothing

## 2) Parent Batch Dependencies
Primary parent batch:
- `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`

Parent artifacts used directly:
- `SOURCE_MAP__v1.md`
- `SIM_CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_SIM_DISTILLATES__v1.md`
- `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
- `MANIFEST.json`

Parent-batch read:
- one result-only orphan surface with no direct runner-name hit
- seq01 absolute baselines plus seq02-04 delta encoding
- hidden `T1` / `T2` lattice axis over explicit direction, init, gate, and repetition keys
- strongest stored delta concentrated on `T1_REV_BELL_CNOT_R1_SEQ04`
- explicit non-equivalence to both the earlier local suite and repo-top `V4` / `V5`
- catalog visibility kept separate from evidence-pack admission

## 3) Candidate Dependency Map
### RC1) `TRAJ_CORR_V2_REMAINS_RESULT_ONLY_AND_RUNNERLESS`
- depends on:
  - parent cluster `A`
  - parent distillates:
    - `D1`
    - `D5`
  - parent candidates:
    - `C1`
    - `C4`
  - parent tension `T1`

### RC2) `SEQ01_BASELINES_AND_SEQ02_04_DELTAS_ARE_THE_STORAGE_CONTRACT`
- depends on:
  - parent clusters:
    - `B`
    - `C`
  - parent distillate `D2`
  - parent candidate `C3`
  - parent tension `T2`

### RC3) `HIDDEN_T_AXIS_AND_STRONGEST_DELTA_CASE_MUST_STAY_ATTACHED`
- depends on:
  - parent clusters:
    - `C`
    - `D`
  - parent distillates:
    - `D2`
    - `D3`
  - parent candidate `C3`
  - parent tension `T5`

### RC4) `CURRENT_ORPHAN_IS_NOT_THE_LOCAL_SUITE_OR_V4_V5`
- depends on:
  - parent cluster `E`
  - parent distillate `D4`
  - parent candidate:
    - `C2`
    - `C5`
  - parent tensions:
    - `T3`
    - `T4`

### RC5) `CATALOG_VISIBILITY_IS_WEAKER_THAN_EVIDENCE_ADMISSION`
- depends on:
  - parent cluster `E`
  - parent distillate `D5`
  - parent tension `T6`

## 4) Quarantine Dependency Map
### Q1) `FAMILY_RESEMBLANCE_AS_INVENTED_RUNNER_ANCHOR`
- depends on:
  - parent distillate `D5`
  - parent candidate `C4`
  - parent tension `T1`

### Q2) `MISSING_SEQ02_04_ABSOLUTES_AS_ABSENT_RUNS`
- depends on:
  - parent distillate `D2`
  - parent tension `T2`

### Q3) `CONTRACT_SHIFT_AS_SIMPLE_VERSION_BUMP`
- depends on:
  - parent distillate `D4`
  - parent candidate `C5`
  - parent tensions:
    - `T3`
    - `T4`

### Q4) `HIDDEN_T_AXIS_ERASURE_AND_GENERIC_DELTA_RETELLING`
- depends on:
  - parent distillate:
    - `D2`
    - `D3`
  - parent tension `T5`

### Q5) `CATALOG_PRESENCE_AS_EVIDENCE_ADMISSION`
- depends on:
  - parent distillate `D5`
  - parent tension `T6`

Quarantine note:
- these residues remain explicit overread risks only in this batch
