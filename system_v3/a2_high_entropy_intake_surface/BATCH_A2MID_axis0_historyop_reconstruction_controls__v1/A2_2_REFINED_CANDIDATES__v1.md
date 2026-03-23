# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_historyop_reconstruction_controls__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_HISTORYOP_PAIRED_FAMILY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_historyop_rec_suite_v1.py` and `results_axis0_historyop_rec_suite_v1.json` should stay compressed as:
  - one standalone residual paired family
  - one runner plus one paired result
  - one bounded family rather than one loose residual file or one multi-pair axis0 omnibus

Why this survives reduction:
- it is the parent batch's cleanest family-identity claim
- it preserves the first residual pair as a reusable unit inside the post-closure lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`
- comparison anchors:
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC1`
  - `BATCH_A2MID_sims_residual_coverage_split__v1:RC3`

Preserved limits:
- this batch does not merge the next residual pair into the current family
- it preserves only this pair as one bounded unit

## Candidate RC2) `FOUR_RECONSTRUCTION_CASE_CLUSTER_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the family is best kept as one shared axis0 history-operator experiment with four internal reconstruction cases:
  - `REC_ID`
  - `REC_MARG`
  - `REC_MIX`
  - `REC_SCR`
- shared trials, cycles, run keys, and sequences stay fixed while reconstruction policy is what changes

Why this survives reduction:
- it is the parent batch's clearest internal structure packet
- it keeps the four-case sweep visible without inflating each case into its own intake family

Source lineage:
- parent cluster `B`
- parent distillate `D2`
- parent candidate summary `C3`

Preserved limits:
- this batch does not flatten the four cases into one identical payload
- it preserves only that they are one bounded case cluster under one family shell

## Candidate RC3) `LOCAL_HISTORYOP_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest evidence-status packet in the parent batch is:
  - the runner emits four explicit local `SIM_EVIDENCE` blocks
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block for any of the four local `SIM_ID`s
- local evidence emission and catalog visibility must stay weaker than repo-top admission

Why this survives reduction:
- it is the parent batch's main visibility contradiction
- later residual summaries need this family kept source-real and locally evidenced without overstating its top-level admission status

Source lineage:
- parent cluster `C`
- parent distillate `D4`
- parent candidate summary `C3`
- parent tension `T1`
- comparison anchors:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`
  - `BATCH_A2MID_sims_residual_coverage_split__v1:RC5`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence and repo-top admission are not the same layer

## Candidate RC4) `RECONSTRUCTION_ERROR_VS_MI_INVARIANCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- reconstruction policy should keep one sharp split:
  - average stored reconstruction error rises strongly from `REC_ID` through `REC_SCR`
  - average stored trajectory `MI` mean stays invariant across all four reconstruction modes

Why this survives reduction:
- it is the parent batch's clearest control-vs-signal packet
- it prevents reconstruction fidelity from being collapsed into the trajectory-MI layer

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D3`
  - `D6`
- parent candidate summary `C4`
- parent tension `T2`

Preserved limits:
- this batch does not deny that reconstruction policy changes one important metric family
- it preserves only that the changed metric family is not the same as stored trajectory `MI`

## Candidate RC5) `SEQUENCE_SIGNAL_WITHOUT_NEGATIVITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the family should preserve one compact signal packet:
  - `SEQ02-SEQ01` trajectory-`MI` deltas stay positive in every case
  - `NEG_SAgB_end_frac` stays exactly `0.0` throughout the stored family
  - even exact reconstruction does not erase the stored sequence-order discriminator

Why this survives reduction:
- it compresses the parent batch's strongest anti-flattening read across `T3` and `T4`
- it keeps order sensitivity visible without forcing any negativity-based story

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D5`
  - `D6`
- parent tensions:
  - `T3`
  - `T4`
- comparison anchor:
  - `BATCH_A2MID_sims_runner_pairing_hygiene__v1:RC6`

Preserved limits:
- this batch does not claim negativity is irrelevant in every sims family
- it preserves only that this family carries sequence signal without stored negative-end-fraction events

## Candidate RC6) `SEQ03_EXTREMUM_OVER_WRITER_SUMMARY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the writer’s compact `SEQ02-SEQ01` summary should stay weaker than the strongest stored extrema because:
  - the strongest stored `MI_traj` and lowest stored `SAgB_end` localize on `SEQ03`
  - those extrema sit at `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`, `BELL_s-1`, `SEQ03`
- compact writer summaries are not the whole numerical story of the family

Why this survives reduction:
- it is the parent batch's clearest anti-summary packet
- later reductions need a compact rule for not overfitting to the emitted headline lines alone

Source lineage:
- parent cluster `A`
- parent distillate `D6`
- parent candidate summary `C5`
- parent tension `T5`

Preserved limits:
- this batch does not deny that the writer summary is useful
- it preserves only that the full stored surface contains stronger local structure than the summary foregrounds

## Quarantined Residue Q1) `LOCAL_EVIDENCE_PLUS_CATALOG_AS_REPOTOP_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- local evidence emission
- catalog visibility
- all treated as if those two facts together upgraded the family into repo-top evidence admission

Why it stays quarantined:
- the parent batch explicitly preserves zero repo-top evidence-pack matches for all four local `SIM_ID`s
- local evidence and catalog visibility are both weaker than repo-top admission

Source lineage:
- parent distillate `D4`
- parent tension `T1`

## Quarantined Residue Q2) `RECONSTRUCTION_ERROR_AS_MI_DRIFT`
Status:
- `QUARANTINED`

Preserved residue:
- higher reconstruction error under lossier rec modes
- all retold as if trajectory `MI` had therefore changed

Why it stays quarantined:
- the parent batch explicitly preserves invariant average stored `MI_traj` means across rec modes
- error drift is weaker than `MI` drift

Source lineage:
- parent distillate `D3`
- parent candidate summary `C4`
- parent tension `T2`

## Quarantined Residue Q3) `NO_NEGATIVITY_AS_NO_SEQUENCE_SIGNAL`
Status:
- `QUARANTINED`

Preserved residue:
- `NEG_SAgB_end_frac = 0.0`
- all retold as if the family therefore had no sequence-order signal

Why it stays quarantined:
- the parent batch explicitly preserves positive `SEQ02-SEQ01` trajectory-`MI` deltas in every case
- no negativity is weaker than no sequence signal

Source lineage:
- parent distillate `D5`
- parent tension `T3`

## Quarantined Residue Q4) `EXACT_RECONSTRUCTION_AS_SIGNAL_ERASURE`
Status:
- `QUARANTINED`

Preserved residue:
- `REC_ID` drives all stored reconstruction errors to `0.0`
- all retold as if that exact reconstruction also erased the family’s sequence discriminator

Why it stays quarantined:
- the parent batch explicitly preserves the strongest stored `dMI_traj_mean_SEQ02_minus_SEQ01` under `REC_ID`
- exact reconstruction removes reconstruction error, not the underlying order signal

Source lineage:
- parent distillate `D6`
- parent tension `T4`

## Quarantined Residue Q5) `WRITER_SEQ02_SEQ01_SUMMARY_AS_COMPLETE_FAMILY_STORY`
Status:
- `QUARANTINED`

Preserved residue:
- the writer’s compact `SEQ02-SEQ01` headline
- all treated as if it exhausted the family’s strongest numerical structure

Why it stays quarantined:
- the parent batch explicitly preserves stronger stored extrema on `SEQ03`
- the compact writer summary is weaker than the full stored result surface

Source lineage:
- parent distillate `D6`
- parent candidate summary `C5`
- parent tension `T5`
