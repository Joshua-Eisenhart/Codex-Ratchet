# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_ab_mi_revival__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_AB_BRANCH_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_mi_discrim_branches_ab.py` and `results_axis0_mi_discrim_branches_ab.json` should stay compressed as:
  - one standalone AB-coupled residual paired family
  - one runner plus one paired result
  - one bounded family rather than one loose residual file or one merged non-AB/AB discriminator block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the AB successor as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`
- comparison anchors:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC1`
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC1`

Preserved limits:
- this batch does not absorb the next residual pair
- it preserves only the current AB pair as one bounded family

## Candidate RC2) `CNOT_COUPLING_MI_REVIVAL_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest executable-to-metric packet in the parent batch is:
  - the AB family adds explicit `CNOT` coupling
  - stored `MI` becomes materially nonzero
  - the family therefore earns the discriminator label only under the changed contract

Why this survives reduction:
- it is the parent batch's clearest contract-dependent signal packet
- later summaries need a compact rule for why the AB successor is not just a rename of the non-AB control

Source lineage:
- parent clusters:
  - `A`
  - `B`
- parent distillate `D2`
- parent candidate summary `C3`
- parent tensions:
  - `T2`
  - `T4`

Preserved limits:
- this batch does not claim the added coupling settles any lower-lane truth
- it preserves only that this contract change is the source-bound difference that revives stored `MI`

## Candidate RC3) `LOCAL_AB_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest evidence-status packet in the parent batch is:
  - the runner emits one explicit local `SIM_EVIDENCE` block
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block for the local `SIM_ID`
  - the runner comment `the fix` stays weaker than repo-top admission

Why this survives reduction:
- it is the parent batch's main visibility contradiction
- later residual summaries need the AB family kept source-real and locally evidenced without overstating its top-level admission status

Source lineage:
- parent cluster `D`
- parent distillate `D4`
- parent candidate summary `C5`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1:RC3`
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence, corrective rhetoric, and repo-top admission are not the same layer

## Candidate RC4) `MI_SIGNAL_WITHOUT_NEGATIVITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the AB family should preserve one compact signal packet:
  - stored `MI` is materially nonzero across both branches
  - `delta_MI_mean_SEQ02_minus_SEQ01` is nonzero
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- the family turns on MI signal without producing any stored negativity event

Why this survives reduction:
- it is the parent batch's clearest MI-without-negativity packet
- it blocks a simplistic equation between nonzero `MI` and negativity onset

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D2`
  - `D5`
- parent tension `T2`

Preserved limits:
- this batch does not claim negativity is irrelevant in every sims family
- it preserves only that this family carries nonzero `MI` without stored negativity onset

## Candidate RC5) `MI_GAIN_WITH_SAGB_ATTENUATION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the comparison to the non-AB control should keep one two-axis shift packet:
  - AB coupling raises `MI` relative to the non-AB sibling
  - AB coupling reduces the absolute `SAgB` branch gap relative to the non-AB sibling
- the successor shift is therefore not one-dimensional

Why this survives reduction:
- it is the parent batch's clearest anti-flattening comparison packet
- later summaries need a compact rule for preserving MI gain and `SAgB` attenuation together

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C4`
- parent tension `T3`
- comparison anchors:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC2`
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC4`

Preserved limits:
- this batch does not deny that both metric families still matter
- it preserves only that their shifts move in different directions under AB coupling

## Candidate RC6) `NONAB_CONTROL_BOUNDARY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the prior non-AB sibling should stay comparison-only here because:
  - it is the control shell without explicit AB coupling
  - it kept `MI` at machine-zero scale
  - the AB family's signal should not be backprojected onto it

Why this survives reduction:
- it is the parent batch's clearest control-versus-successor boundary
- later residual work needs a compact rule for keeping the two families adjacent but separate

Source lineage:
- parent cluster `C`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C5`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC5`

Preserved limits:
- this batch does not deny that the families are directly comparable
- it preserves only that comparison is weaker than merger or backprojection

## Quarantined Residue Q1) `THE_FIX_COMMENT_AS_REPOTOP_ADMISSION_OR_CANONIZATION`
Status:
- `QUARANTINED`

Preserved residue:
- the runner labels the added `CNOT` as `the fix`
- all retold as if that local comment established repo-top admission or canonization

Why it stays quarantined:
- the parent batch explicitly preserves zero repo-top evidence-pack matches for the local `SIM_ID`
- corrective rhetoric is weaker than evidence admission

Source lineage:
- parent distillate `D6`
- parent candidate summary `C5`
- parent tension `T1`

## Quarantined Residue Q2) `NONZERO_MI_AS_NEGATIVITY_ONSET`
Status:
- `QUARANTINED`

Preserved residue:
- nonzero stored `MI`
- all retold as if negativity had therefore appeared

Why it stays quarantined:
- the parent batch explicitly preserves `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- nonzero `MI` is weaker than negativity onset

Source lineage:
- parent distillates:
  - `D2`
  - `D5`
- parent tension `T2`

## Quarantined Residue Q3) `AB_COUPLING_AS_ONE_DIMENSIONAL_METRIC_IMPROVEMENT`
Status:
- `QUARANTINED`

Preserved residue:
- AB coupling raises `MI`
- all retold as if every branch-discriminator metric therefore improved in the same direction

Why it stays quarantined:
- the parent batch explicitly preserves `SAgB` attenuation relative to the non-AB control
- MI gain is weaker than one-dimensional metric improvement

Source lineage:
- parent distillate `D3`
- parent candidate summary `C4`
- parent tension `T3`

## Quarantined Residue Q4) `AB_SIGNAL_BACKPROJECTED_ONTO_NONAB_CONTROL`
Status:
- `QUARANTINED`

Preserved residue:
- the AB family's nonzero `MI`
- all retold as if the prior non-AB control already carried that same signal

Why it stays quarantined:
- the parent batch explicitly preserves the non-AB sibling as machine-zero on the `MI` layer
- successor signal is weaker than control-family retroactive reinterpretation

Source lineage:
- parent distillate `D6`
- parent tension `T4`

## Quarantined Residue Q5) `COMPACT_BRANCH_MEANS_AS_FULL_DYNAMIC_PROOF`
Status:
- `QUARANTINED`

Preserved residue:
- compact branch-level means and deltas
- all treated as if they fully proved the family’s richer dynamics

Why it stays quarantined:
- the parent batch explicitly preserves only compact branch summaries
- compact summaries are weaker than full dynamic structure

Source lineage:
- parent distillate `D6`
- parent tension `T5`
