# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_engine32_delta_absolute_fences__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `ENGINE32_SINGLE_LATTICE_FAMILY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `engine32_axis0_axis6_attack` is best kept as:
  - one focused `2 x 4 x 2 x 2` attack lattice
  - one SIM_ID
  - one paired result family
  - one direct executable/result surface rather than a composite precursor bundle

Why this survives reduction:
- it is the parent batch's clearest family-identity claim
- later sims lineage work needs this direct-family boundary before any interpretation of deltas or Axis labels

Source lineage:
- parent cluster `S1`
- parent distillate `D1`
- parent candidate `C1`

Preserved limits:
- this batch does not treat engine32 as a cross-axis sampler
- this batch does not inflate the family beyond its single stored lattice

## Candidate RC2) `AXIS0_PROXY_NO_AB_COUPLING_FENCE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the parent batch's safest Axis0 reading is:
  - the file carries an `Axis0 attack` label
  - the implementation explicitly narrows that label to a one-qubit trajectory proxy
  - `No AB coupling in this batch` remains an active scope fence

Why this survives reduction:
- it is the sharpest anti-overread boundary in the parent batch
- it preserves the label and the implementation limit together instead of letting either erase the other

Source lineage:
- parent cluster `S2`
- parent distillate `D3`
- parent candidate `C4`
- parent tension `T1`

Preserved limits:
- this batch does not treat engine32 as AB-correlation evidence
- this batch preserves proxy scope rather than resolving the label away

## Candidate RC3) `ABSOLUTE_32_CELL_RESULT_OVER_DELTA_ONLY_EVIDENCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the reconstructable surface for engine32 is:
  - the paired JSON with absolute stage metrics across all `32` cells
  - not the script-local evidence block alone
- the evidence block is narrower:
  - `MIX_R - UNIFORM` deltas only
  - one compressed sidecar view rather than the full stored lattice

Why this survives reduction:
- it is the parent batch's strongest evidence-shape seam
- later provenance and interpretation work needs a compact rule for not mistaking compressed delta output for the complete result surface

Source lineage:
- parent cluster `S4`
- parent distillate `D4`
- parent candidate `C3`
- parent tension `T2`
- comparison anchors:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_batch_v3_precursor_lineage__v1:RC2`

Preserved limits:
- this batch does not demote the evidence block to uselessness
- it only preserves that the evidence block is not the whole stored family

## Candidate RC4) `LOOP_ORIENTATION_SIGN_SPLIT_BEFORE_SEQUENCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest stored signal in engine32 is loop orientation:
  - outer `MIX_R` entropy deltas stay positive and purity deltas stay negative
  - inner `MIX_R` entropy deltas stay negative and purity deltas stay positive
- sequence order still matters, but mainly as magnitude modulation inside that stronger split

Why this survives reduction:
- it is the parent batch's clearest numerical ordering rule
- it keeps the family interpretable without overpromoting one sequence-specific cell

Source lineage:
- parent cluster `S3`
- parent distillate `D2`
- parent candidate `C2`
- parent tension `T3`

Preserved limits:
- this batch does not erase sequence variation
- it only keeps sequence detail subordinate to the stronger outer/inner sign split

## Candidate RC5) `CATALOG_PRESENT_SCRIPTLOCAL_EVIDENCE_NOT_TOPLEVEL_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- engine32 currently sits behind three different provenance layers:
  - catalog-visible family presence
  - script-local evidence emission capability
  - missing current top-level evidence-pack block
- those layers must stay separate when grading confidence or downstream admissibility

Why this survives reduction:
- it is the parent batch's cleanest provenance/admission caution
- it preserves source-local visibility without overstating repo-top-level admission strength

Source lineage:
- parent cluster `S5`
- parent distillate `D5`
- parent tensions:
  - `T4`
  - `T6`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`

Preserved limits:
- this batch does not deny that local evidence exists
- it preserves only that local evidence and catalog presence do not equal current top-level admission

## Candidate RC6) `FULL_AXIS_SAMPLER_ADJACENCY_SEPARATION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the adjacent `full_axis_suite` file remains separate because:
  - engine32 is one focused attack lattice
  - `full_axis_suite` is a multi-block cross-axis sampler
  - shared axis vocabulary and raw-order adjacency are not enough to merge them into one family

Why this survives reduction:
- it preserves the parent batch's clean family-boundary decision
- it keeps the next raw-order sampler available for its own bounded reduction step

Source lineage:
- parent cluster `S6`
- parent distillate `D6`
- parent candidates:
  - `C5`
  - `C6`
- parent tension `T5`

Preserved limits:
- this batch does not import sampler semantics into engine32
- this batch does not settle the sampler's own descendant story here

## Quarantined Residue Q1) `AXIS0_ATTACK_LABEL_AS_AB_COUPLED_AXIS0_EVIDENCE`
Status:
- `QUARANTINED`

Preserved residue:
- the `Axis0 attack` label
- treated as if it already proved AB-coupled Axis0 evidence

Why it stays quarantined:
- the parent batch explicitly preserves a one-qubit proxy with no AB coupling
- the label alone is too weak to override the implementation fence

Source lineage:
- parent cluster `S2`
- parent distillate `D3`
- parent tension `T1`

## Quarantined Residue Q2) `DELTA_SIDECAR_AS_COMPLETE_RESULT_SURFACE`
Status:
- `QUARANTINED`

Preserved residue:
- the emitted evidence block
- treated as if it fully represented every stored engine32 result cell

Why it stays quarantined:
- the parent batch explicitly separates compressed deltas from the richer absolute JSON lattice
- this overread would erase the main evidence-shape seam

Source lineage:
- parent cluster `S4`
- parent distillate `D4`
- parent tension `T2`

## Quarantined Residue Q3) `SEQUENCE_ORDER_AS_PRIMARY_SIGNAL`
Status:
- `QUARANTINED`

Preserved residue:
- sequence-specific magnitude variation
- treated as if it were the family's main signal instead of the loop split

Why it stays quarantined:
- the parent batch explicitly preserves sequence variation under a stronger stable outer/inner sign pattern
- promoting sequence first would flatten the dominant orientation signature

Source lineage:
- parent cluster `S3`
- parent distillate `D2`
- parent tension `T3`

## Quarantined Residue Q4) `CATALOG_OR_SCRIPTLOCAL_EVIDENCE_AS_REPO_TOPLEVEL_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- catalog visibility
- script-local evidence emission
- all treated as if they already yielded current top-level evidence-pack admission

Why it stays quarantined:
- the parent batch explicitly preserves absence of a current direct top-level engine32 block
- provenance visibility and admission are not the same layer

Source lineage:
- parent cluster `S5`
- parent distillate `D5`
- parent tensions:
  - `T4`
  - `T6`

## Quarantined Residue Q5) `ENGINE32_AND_FULL_AXIS_SAMPLER_MERGED_BY_ADJACENCY`
Status:
- `QUARANTINED`

Preserved residue:
- shared axis vocabulary
- raw-order adjacency
- all treated as if engine32 and `full_axis_suite` belonged to one family

Why it stays quarantined:
- the parent batch explicitly keeps the focused attack lattice and the cross-axis sampler separate
- adjacency is not enough to erase structural family boundaries

Source lineage:
- parent cluster `S6`
- parent tension `T5`
- parent candidate `C5`
