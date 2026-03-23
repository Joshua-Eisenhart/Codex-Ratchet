# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE-LINKED REDUCTION MAP
Batch: `BATCH_A2MID_sims_axis0_boundary_bookkeep_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## 1) Reduction Scope
This A2-mid batch narrows one existing sims orphan intake batch into controller-usable provenance, enrichment, evidence-boundary, and anti-merge fences.

Reduction rule used here:
- no raw-source reread
- no runtime execution
- no active A2 append-save
- no contradiction smoothing

## 2) Parent Batch Dependencies
Primary parent batch:
- `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`

Parent artifacts used directly:
- `SOURCE_MAP__v1.md`
- `SIM_CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_SIM_DISTILLATES__v1.md`
- `A2_2_SIM_CANDIDATE_SUMMARIES__v1.md`
- `MANIFEST.json`

Parent-batch read:
- one result-only orphan surface with exact overlap to an already-batched sweep-family slice
- local enrichment beyond the overlapping sweep means
- strong BELL-vs-GINIBRE bookkeeping separation with stored zero negativity
- explicit separation from the catalog-adjacent `traj_corr_suite_v2` orphan
- catalog visibility kept separate from evidence-pack admission

## 3) Candidate Dependency Map
### RC1) `ORPHAN_SLICE_REMAINS_BOUNDED_BUT_SWEEP_ANCHORED`
- depends on:
  - parent clusters:
    - `A`
    - `C`
  - parent distillates:
    - `D1`
    - `D2`
  - parent candidates:
    - `C1`
    - `C4`
  - parent tension `T1`

### RC2) `ENRICHED_SLICE_NOT_REDUNDANT_DUPLICATE`
- depends on:
  - parent cluster `C`
  - parent distillates:
    - `D2`
    - `D3`
  - parent tension `T2`

### RC3) `BELL_GINIBRE_BOOKKEEPING_SPLIT_WITH_ZERO_NEGATIVITY`
- depends on:
  - parent cluster `B`
  - parent distillate `D4`
  - parent candidate `C3`
  - parent tension `T3`

### RC4) `TRAJ_CORR_V2_STAYS_A_SEPARATE_RESIDUAL_FAMILY`
- depends on:
  - parent cluster `D`
  - parent distillate `D1`
  - parent candidates:
    - `C2`
    - `C5`
    - `C6`
  - parent tension `T4`

### RC5) `CATALOG_VISIBILITY_IS_WEAKER_THAN_EVIDENCE_ADMISSION_AND_FAMILY_ANCHOR`
- depends on:
  - parent cluster `E`
  - parent distillate `D5`
  - parent tension:
    - `T5`
    - `T6`

## 4) Quarantine Dependency Map
### Q1) `ORPHAN_STATUS_AS_SOURCE_UNANCHORED`
- depends on:
  - parent distillate `D2`
  - parent candidate `C4`
  - parent tension `T1`

### Q2) `EXACT_SWEEP_OVERLAP_AS_REDUNDANT_DUPLICATE`
- depends on:
  - parent distillate `D3`
  - parent tension `T2`

### Q3) `CATALOG_ADJACENCY_AS_MERGE_PERMISSION`
- depends on:
  - parent candidate `C2`
  - parent candidate `C5`
  - parent tension `T4`

### Q4) `LARGE_BOOKKEEPING_DISPLACEMENT_AS_NEGATIVITY_PROOF`
- depends on:
  - parent distillate `D4`
  - parent tension `T3`

### Q5) `CATALOG_PRESENCE_AS_EVIDENCE_PACK_ADMISSION`
- depends on:
  - parent distillate `D5`
  - parent tension `T5`

Quarantine note:
- these residues remain explicit overread risks only in this batch
