# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_NONAB_BRANCH_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_mi_discrim_branches.py` and `results_axis0_mi_discrim_branches.json` should stay compressed as:
  - one standalone non-AB residual paired family
  - one runner plus one paired result
  - one bounded family rather than one loose residual file or one merged non-AB/AB discriminator block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the second residual pair as its own reusable unit

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`
- comparison anchors:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC1`
  - `BATCH_A2MID_sims_residual_coverage_split__v1:RC3`

Preserved limits:
- this batch does not absorb the `_ab` sibling
- it preserves only the current non-AB pair as one bounded family

## Candidate RC2) `MI_NAME_WITH_SAGB_REALITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest interpretation packet in the parent batch is:
  - the file is named as an MI discriminator
  - stored `MI` means and `delta_MI_mean_SEQ02_minus_SEQ01` stay at machine-zero scale
  - the actual stored branch split appears in `delta_SAgB_mean_SEQ02_minus_SEQ01`

Why this survives reduction:
- it is the parent batch's clearest naming-versus-metric contradiction
- later summaries need a compact rule for not taking the filename as the metric truth

Source lineage:
- parent cluster `B`
- parent distillate `D2`
- parent candidate summaries:
  - `C3`
  - `C4`
- parent tension `T2`

Preserved limits:
- this batch does not deny that `MI` is present as a measured field
- it preserves only that the stored non-AB discriminator is materially in `SAgB`, not `MI`

## Candidate RC3) `LOCAL_NONAB_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest evidence-status packet in the parent batch is:
  - the runner emits one explicit local `SIM_EVIDENCE` block
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block for the local `SIM_ID`
- local evidence emission and catalog visibility must stay weaker than repo-top admission

Why this survives reduction:
- it is the parent batch's main visibility contradiction
- later residual summaries need the family kept source-real and locally evidenced without overstating its top-level admission status

Source lineage:
- parent cluster `D`
- parent distillate `D4`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC3`
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence and repo-top admission are not the same layer

## Candidate RC4) `SAGB_BRANCH_SPLIT_WITH_ZERO_NEGATIVITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the non-AB family should preserve one compact branch-sensitivity packet:
  - `delta_SAgB_mean_SEQ02_minus_SEQ01` is nonzero
  - both stored branches keep `neg_SAgB_frac = 0.0`
- branch sensitivity is present without any stored negative conditional-entropy event

Why this survives reduction:
- it is the parent batch's clearest non-AB branch-signal packet
- it keeps zero negativity from being misread as total invariance

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D2`
  - `D5`
- parent tension `T4`

Preserved limits:
- this batch does not claim negativity is unnecessary in all families
- it preserves only that this family carries a branch split without stored negativity

## Candidate RC5) `AB_SIBLING_MI_REVIVAL_BOUNDARY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the adjacent `_ab` sibling should stay comparison-only here because:
  - it adds explicit AB coupling via `CNOT`
  - it revives materially nonzero stored `MI` means and `delta_MI`
  - that change is strong enough to begin the next bounded family instead of extending the current one

Why this survives reduction:
- it is the parent batch's clearest anti-merge boundary
- later residual work needs a compact rule for why the non-AB and AB variants cannot be collapsed

Source lineage:
- parent cluster `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C5`
- parent tension `T3`

Preserved limits:
- this batch does not deny the naming adjacency between the two files
- it preserves only that executable coupling and stored metric behavior make the sibling a separate family

## Candidate RC6) `COMPACT_RESULT_SURFACE_SIGNAL_STRENGTH_CAUTION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the compact result surface should stay weaker than strong-signal rhetoric because:
  - it stores only branch-level summary statistics
  - it still foregrounds MI deltas even while the stored MI layer is effectively machine-zero
- compact evidence formatting is not the same as substantive signal strength

Why this survives reduction:
- it is the parent batch's clearest anti-overread packet for small result surfaces
- later reductions need a compact rule for not equating formatted delta fields with meaningful magnitude

Source lineage:
- parent cluster `B`
- parent distillate `D6`
- parent tension `T5`

Preserved limits:
- this batch does not deny that the result surface is useful
- it preserves only that compactness and explicit delta fields do not by themselves prove strong MI movement

## Quarantined Residue Q1) `LOCAL_EVIDENCE_PLUS_CATALOG_AS_REPOTOP_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- local evidence emission
- catalog visibility
- all treated as if those two facts together upgraded the family into repo-top evidence admission

Why it stays quarantined:
- the parent batch explicitly preserves zero repo-top evidence-pack matches for the local `SIM_ID`
- local evidence and catalog visibility are both weaker than repo-top admission

Source lineage:
- parent distillate `D4`
- parent tension `T1`

## Quarantined Residue Q2) `MI_DISCRIMINATOR_NAME_AS_MATERIAL_MI_SIGNAL`
Status:
- `QUARANTINED`

Preserved residue:
- the file name and writer posture say `MI discriminator`
- all retold as if the stored non-AB `MI` layer were materially nonzero

Why it stays quarantined:
- the parent batch explicitly preserves machine-scale `MI` means and `delta_MI`
- the name is weaker than the stored metric surface

Source lineage:
- parent distillate `D2`
- parent candidate summary `C4`
- parent tension `T2`

## Quarantined Residue Q3) `ZERO_NEGATIVITY_AS_TOTAL_BRANCH_INVARIANCE`
Status:
- `QUARANTINED`

Preserved residue:
- both branches keep `neg_SAgB_frac = 0.0`
- all retold as if the family therefore had no real branch discrimination

Why it stays quarantined:
- the parent batch explicitly preserves a nonzero `SAgB` branch split
- zero negativity is weaker than total metric invariance

Source lineage:
- parent distillate `D5`
- parent tension `T4`

## Quarantined Residue Q4) `NONAB_AND_AB_SIBLING_AS_ONE_FAMILY`
Status:
- `QUARANTINED`

Preserved residue:
- the current non-AB family
- the adjacent `_ab` sibling
- all treated as if naming proximity alone made them one bounded family

Why it stays quarantined:
- the parent batch explicitly preserves material executable and metric differences once AB coupling is added
- naming adjacency is weaker than contract and signal differences

Source lineage:
- parent distillate `D3`
- parent candidate summary `C5`
- parent tension `T3`

## Quarantined Residue Q5) `COMPACT_RESULT_FORMAT_AS_STRONG_MI_PROOF`
Status:
- `QUARANTINED`

Preserved residue:
- explicit delta fields in a compact result surface
- all treated as if their presence alone proved strong MI movement

Why it stays quarantined:
- the parent batch explicitly preserves machine-scale `MI` values despite the formatting
- compact output structure is weaker than substantive signal magnitude

Source lineage:
- parent distillate `D6`
- parent tension `T5`
