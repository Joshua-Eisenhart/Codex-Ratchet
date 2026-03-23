# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_sims_axis0_boundary_bookkeep_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `ORPHAN_SLICE_REMAINS_BOUNDED_BUT_SWEEP_ANCHORED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current axis0 boundary/bookkeep orphan should be read as:
  - one bounded result-only orphan slice
  - with exact overlap to the already-batched sweep family
  - and therefore not source-unanchored

Why this survives reduction:
- it is the parent batch's strongest provenance rule
- it keeps the orphan bounded without letting orphan status erase exact family anchoring

Source lineage:
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

Preserved limits:
- this batch does not merge the orphan into the wider sweep family
- it preserves only that the orphan is bounded and exactly anchored

## Candidate RC2) `ENRICHED_SLICE_NOT_REDUNDANT_DUPLICATE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the current orphan is not just a duplicate sweep excerpt because it keeps:
  - exact overlap on shared mean metrics
  - plus local extrema fields and zero-negativity fields absent from the matching sweep slice

Why this survives reduction:
- it is the parent batch's clearest anti-redundancy fence
- it prevents exact overlap from flattening away the local enrichment

Source lineage:
- parent cluster `C`
- parent distillates:
  - `D2`
  - `D3`
- parent tension `T2`

Preserved limits:
- this batch does not claim the enrichment makes the orphan a new standalone family
- it preserves only that local enrichment is real and should stay visible

## Candidate RC3) `BELL_GINIBRE_BOOKKEEPING_SPLIT_WITH_ZERO_NEGATIVITY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest local result packet in the orphan is:
  - materially larger bookkeeping displacement on BELL than on GINIBRE
  - while all stored negativity fractions remain zero across the slice

Why this survives reduction:
- it is the parent batch's sharpest compact result read
- it keeps displacement magnitude separate from negativity claims

Source lineage:
- parent cluster `B`
- parent distillate `D4`
- parent candidate `C3`
- parent tension `T3`

Preserved limits:
- this batch does not generalize beyond the stored sign1 / REC1 slice
- it preserves only the local split and zero-negativity boundary in the current result surface

## Candidate RC4) `TRAJ_CORR_V2_STAYS_A_SEPARATE_RESIDUAL_FAMILY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `results_axis0_traj_corr_suite_v2.json` must stay outside this orphan batch because it carries:
  - a different lattice
  - a different metric contract
  - a broader trajectory-correlation surface
  - and no license to merge on catalog adjacency alone

Why this survives reduction:
- it is the parent batch's strongest anti-merge and sequencing rule
- it keeps the next residual follow-on bounded instead of collapsing adjacent axis0 orphans together

Source lineage:
- parent cluster `D`
- parent distillate `D1`
- parent candidates:
  - `C2`
  - `C5`
  - `C6`
- parent tension `T4`

Preserved limits:
- this batch does not deny that the deferred orphan is related to the same broad axis0 neighborhood
- it preserves only that relatedness is weaker than clean family identity

## Candidate RC5) `CATALOG_VISIBILITY_IS_WEAKER_THAN_EVIDENCE_ADMISSION_AND_FAMILY_ANCHOR`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the controller should keep one visibility rule here:
  - catalog listing is weaker than evidence-pack admission
  - and both are weaker than the current orphan's exact sweep-family anchor for source trust

Why this survives reduction:
- it is the parent batch's cleanest evidence-boundary packet
- it prevents filename visibility from being retold as maintained evidence admission

Source lineage:
- parent cluster `E`
- parent distillate `D5`
- parent tension:
  - `T5`
  - `T6`

Preserved limits:
- this batch does not deny that catalog visibility is still useful
- it preserves only that catalog listing and evidence admission are not interchangeable

## Quarantined Residue Q1) `ORPHAN_STATUS_AS_SOURCE_UNANCHORED`
Status:
- `QUARANTINED`

Preserved residue:
- the current file is a result-only orphan
- all retold as if it therefore lacked a real family anchor

Why it stays quarantined:
- the parent batch preserves exact overlap to the already-batched sweep family
- orphan status is weaker than source-anchor absence

Source lineage:
- parent distillate `D2`
- parent candidate `C4`
- parent tension `T1`

## Quarantined Residue Q2) `EXACT_SWEEP_OVERLAP_AS_REDUNDANT_DUPLICATE`
Status:
- `QUARANTINED`

Preserved residue:
- shared means match exactly
- all retold as if the orphan added nothing locally

Why it stays quarantined:
- the parent batch explicitly preserves extra extrema and zero-negativity fields
- exact overlap is weaker than full redundancy

Source lineage:
- parent distillate `D3`
- parent tension `T2`

## Quarantined Residue Q3) `CATALOG_ADJACENCY_AS_MERGE_PERMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- the neighboring `traj_corr_suite_v2` orphan sits nearby in catalog space
- all retold as if adjacency alone licensed one merged family

Why it stays quarantined:
- the parent batch explicitly preserves lattice and metric-contract separation
- adjacency is weaker than bounded family identity

Source lineage:
- parent candidates:
  - `C2`
  - `C5`
- parent tension `T4`

## Quarantined Residue Q4) `LARGE_BOOKKEEPING_DISPLACEMENT_AS_NEGATIVITY_PROOF`
Status:
- `QUARANTINED`

Preserved residue:
- strong bookkeeping displacement on BELL
- all retold as if the slice therefore carried negativity production

Why it stays quarantined:
- the stored negativity fractions stay zero throughout the orphan
- displacement magnitude is weaker than negativity evidence

Source lineage:
- parent distillate `D4`
- parent tension `T3`

## Quarantined Residue Q5) `CATALOG_PRESENCE_AS_EVIDENCE_PACK_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- the current orphan is catalog-listed
- all retold as if the evidence pack therefore admitted the same family

Why it stays quarantined:
- the parent batch explicitly preserves evidence-pack omission for both the current orphan and the deferred trajectory orphan
- catalog listing is weaker than evidence admission

Source lineage:
- parent distillate `D5`
- parent tension `T5`
