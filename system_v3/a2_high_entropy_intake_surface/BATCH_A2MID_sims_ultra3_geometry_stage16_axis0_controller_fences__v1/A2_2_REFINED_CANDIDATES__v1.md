# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_sims_ultra3_geometry_stage16_axis0_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `ULTRA3_REMAINS_RESULT_ONLY_CATALOG_VISIBLE_AND_RUNNERLESS`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should keep three provenance limits together:
  - the current ultra3 family remains one bounded result-only orphan surface
  - it is catalog-visible by filename alias
  - no runner is admitted as a source member and evidence-pack admission remains absent

Why this survives reduction:
- it is the parent batch's strongest provenance rule
- it prevents catalog visibility from being retold as executable provenance

Source lineage:
- parent cluster `A`
- parent distillates:
  - `D1`
  - `D5`
- parent candidates:
  - `C1`
  - `C2`
- parent tension `T1`

Preserved limits:
- this batch does not deny that catalog visibility is useful
- it preserves only that visibility is weaker than runner anchoring and evidence admission

## Candidate RC2) `BERRY_FLUX_SIGN_SYMMETRY_DOES_NOT_YIELD_EXACT_2PI_OR_ULTRA4_IDENTITY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should preserve that ultra3 carries exact sign symmetry at stored precision while still blocking two overreads:
  - exact `±2pi` inflation
  - identity with ultra4 merely because both surfaces carry geometry

Why this survives reduction:
- it is the parent batch's clearest geometry-boundary rule
- it keeps exact sign symmetry while refusing magnitude and family-identity inflation

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D2`
  - `D6`
- parent candidate `C3`
- parent tensions:
  - `T3`
  - `T5`

Preserved limits:
- this batch does not deny geometry continuity
- it preserves only that continuity is weaker than exact magnitude identity and family equivalence

## Candidate RC3) `STAGE16_SMALL_SE_CENTER_AND_AXIS0AB_LARGE_LATTICE_MUST_STAY_SEPARATE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should keep one macro-shell rule here:
  - the file is one ultra3 surface
  - but its Se-centered `stage16` branch and its larger `axis0_ab` branch live on materially different effect scales and must not be averaged into one uniform story

Why this survives reduction:
- it is the parent batch's strongest anti-flattening branch-scale packet
- it keeps the Se-centered stage16 concentration attached to the larger axis0_ab delta lattice rather than burying both in one blended summary

Source lineage:
- parent clusters:
  - `C`
  - `D`
- parent distillate `D3`
- parent candidate `C3`
- parent tension `T4`

Preserved limits:
- this batch does not infer theory from one extremum
- it preserves only that branch-specific scales and strongest cells must stay explicit

## Candidate RC4) `AXIS0AB_SEQ01_BASELINES_AND_SEQ02_04_DELTAS_ARE_THE_STORAGE_CONTRACT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should preserve that the `axis0_ab` lattice uses a mixed contract:
  - `SEQ01` stores absolute baselines
  - `SEQ02-04` store deltas
  - summaries therefore must keep baseline-vs-relative record type separation explicit

Why this survives reduction:
- it is the parent batch's clearest storage-contract rule
- it prevents the current lattice from being retold as one flat record schema

Source lineage:
- parent cluster `D`
- parent distillates:
  - `D2`
  - `D6`
- parent candidate `C3`
- parent tension `T2`

Preserved limits:
- this batch does not reconstruct missing absolutes for `SEQ02-04`
- it preserves only that delta encoding is the intended stored contract

## Candidate RC5) `ULTRA3_IS_A_MIDDLE_SEAM_NOT_ULTRA4_NOT_THE_FINAL_SWEEP`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should keep ultra3 as a middle seam:
  - it stays near the earlier ultra strip by structure
  - it keeps geometry like ultra4 while dropping `axis12`
  - it keeps `stage16` plus `axis0_ab` like the final sweep while retaining geometry the sweep lacks

Why this survives reduction:
- it is the parent batch's strongest anti-merge family-boundary rule
- it preserves structural continuity without collapsing ultra3 into any one already-batched ultra family

Source lineage:
- parent cluster `E`
- parent distillates:
  - `D4`
  - `D6`
- parent candidates:
  - `C4`
  - `C5`
- parent tension `T5`

Preserved limits:
- this batch does not deny ultra-strip continuity
- it preserves only that continuity is weaker than family identity

## Candidate RC6) `ULTRABIG_REMAINS_THE_NEXT_BOUNDED_FAMILY_AND_CATALOG_ADJACENCY_IS_NOT_A_MERGE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- controller reads should keep `ultra_big_ax012346` outside the current packet because it omits berry flux, `stage16`, and the `128`-entry `axis0_ab` lattice, so catalog adjacency points to the next bounded family rather than a merge permission

Why this survives reduction:
- it is the parent batch's cleanest handoff and nonmerge rule
- it keeps the next residual pass explicit without dissolving the current family boundary

Source lineage:
- parent cluster `F`
- parent distillates:
  - `D5`
  - `D6`
- parent candidates:
  - `C5`
  - `C6`
- parent tensions:
  - `T1`
  - `T6`

Preserved limits:
- this batch does not deny that ultra_big is nearby in the catalog
- it preserves only that adjacency is weaker than bounded-family identity

## Quarantined Residue Q1) `CATALOG_PRESENCE_AS_EVIDENCE_ADMISSION_OR_RUNNER_PROVENANCE`
Status:
- `QUARANTINED`

Preserved residue:
- the current ultra3 orphan is catalog-listed
- all retold as if the repo-held evidence pack or an admitted runner therefore exists

Why it stays quarantined:
- the parent batch explicitly preserves evidence omission and no-runner source membership
- catalog visibility is weaker than admitted provenance

Source lineage:
- parent distillate `D5`
- parent tensions:
  - `T1`
  - `T6`

## Quarantined Residue Q2) `BERRY_FLUX_AS_EXACT_2PI_OR_ULTRA4_EQUIVALENCE`
Status:
- `QUARANTINED`

Preserved residue:
- berry flux is sign-symmetric at stored precision
- all retold as if the magnitude is exactly `±2pi` or therefore identical to ultra4

Why it stays quarantined:
- the parent batch explicitly preserves approximate magnitude and non-identity with ultra4
- sign symmetry is weaker than exact quantization and family equivalence

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent tension `T3`

## Quarantined Residue Q3) `ONE_UNIFORM_SCALE_OR_ONE_UNIFORM_RECORD_CONTRACT`
Status:
- `QUARANTINED`

Preserved residue:
- stage16 and axis0_ab behavior are discussed
- all retold as if the file has one effect scale and one flat record contract

Why it stays quarantined:
- the parent batch explicitly preserves both the branch-scale split and the seq01-baseline-vs-seq02-04-delta contract
- flattening is weaker than the stored structure

Source lineage:
- parent distillates:
  - `D2`
  - `D3`
  - `D6`
- parent tensions:
  - `T2`
  - `T4`

## Quarantined Residue Q4) `ULTRA3_AS_DUPLICATE_OF_ULTRA4_OR_THE_FINAL_SWEEP`
Status:
- `QUARANTINED`

Preserved residue:
- ultra3 shares part of the ultra4 and final-sweep contracts
- all retold as if that shared structure erases the middle-seam boundary

Why it stays quarantined:
- the parent batch explicitly preserves seam continuity without family identity
- partial overlap is weaker than bounded-family equivalence

Source lineage:
- parent distillate `D4`
- parent candidate `C4`
- parent tension `T5`

## Quarantined Residue Q5) `ULTRABIG_MERGE_FROM_CATALOG_ADJACENCY`
Status:
- `QUARANTINED`

Preserved residue:
- ultra_big sits next in the catalog
- all retold as if that adjacency justifies merging it into the current ultra3 family

Why it stays quarantined:
- the parent batch explicitly preserves different branch contracts and a separate next-family handoff
- catalog adjacency is weaker than bounded-family separation

Source lineage:
- parent distillates:
  - `D5`
  - `D6`
- parent candidate `C5`
- parent tension `T6`
