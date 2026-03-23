# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_negsagb_search_failure__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_NEGSAGB_STRESS_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_negsagb_stress.py` and `results_axis0_negsagb_stress.json` should stay compressed as:
  - one standalone axis0 negativity-stress residual pair
  - one runner plus one paired result
  - one bounded family rather than one merged baseline-plus-search block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the stress pair as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not absorb the smaller mutual-information baseline
- it preserves only the current stress pair as one bounded family

## Candidate RC2) `FULL_GRID_ZERO_SCORE_EXHAUSTION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest execution-versus-outcome seam in the parent batch is:
  - the runner covers a `3456`-record grid
  - the early-stop threshold is `best.score >= 0.05`
  - the stored run still ends with:
    - `records_count = 3456`
    - `best.score = 0.0`

Why this survives reduction:
- it is the parent batch's clearest failure packet
- later summaries need a compact rule for describing this family as a completed search that failed its own negativity objective

Source lineage:
- parent cluster `B`
- parent distillate `D2`
- parent candidate summary `C3`
- parent tension `T1`

Preserved limits:
- this batch does not claim the search was incomplete
- it preserves only that exhaustive search and search success are different claims

## Candidate RC3) `BEST_PLUS_SAMPLE_RETENTION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the stored result surface should preserve one compression packet:
  - the runner executes the whole grid
  - the retained output keeps:
    - one `best` record
    - `records_sample[:10]`
  - the stored surface is not the full trace

Why this survives reduction:
- it is the parent batch's clearest storage-granularity seam
- later summaries need a compact rule for not confusing retained output with the full search table

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D2`
  - `D3`
- parent candidate summary `C3`
- parent tension `T3`

Preserved limits:
- this batch does not deny that `best` and the sample are useful
- it preserves only that they are weaker than full-trace retention

## Candidate RC4) `LOCAL_STRESS_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest evidence-status packet in the parent batch is:
  - the catalog lists the family
  - the runner emits a local evidence block
  - the repo-held top-level evidence pack omits the local `SIM_ID`
- local evidence and catalog visibility must stay weaker than repo-top admission

Why this survives reduction:
- it is the parent batch's main visibility contradiction
- later residual summaries need the family kept source-real and locally evidenced without overstating its repo-top status

Source lineage:
- parent cluster `E`
- parent distillate `D4`
- parent tension `T5`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence, catalog presence, and repo-top admission are not the same layer

## Candidate RC5) `BASELINE_OUTPERFORMS_STRESS_ON_NEGATIVITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the comparison to the smaller mutual-information baseline should keep one inversion packet:
  - the larger stress sweep stores `best.score = 0.0` and zero best-record negativity fraction
  - the smaller baseline stores:
    - `neg_SAgB_frac = 0.001953125`
    - `SAgB_min = -0.002114071978150056`
- the larger search family does not automatically outrank the smaller baseline on stored negativity evidence

Why this survives reduction:
- it is the parent batch's clearest anti-supersession packet
- later backlog work needs a compact rule for preserving this inversion before entering the next residual pair

Source lineage:
- parent clusters:
  - `D`
  - `E`
- parent distillates:
  - `D4`
  - `D6`
- parent candidate summary `C5`
- parent tension `T2`
- comparison anchor:
  - `BATCH_A2MID_axis0_mutualinfo_killgate_boundary__v1:RC5`

Preserved limits:
- this batch does not deny that the stress family is broader
- it preserves only that breadth does not automatically beat the smaller stored baseline result

## Candidate RC6) `MICRO_DELTAS_DO_NOT_REDEEM_ZERO_SCORE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the best record should preserve one anti-redemption packet:
  - `delta_MI_mean_SEQ02_minus_SEQ01 = -0.00030116171275254566`
  - `delta_SAgB_mean_SEQ02_minus_SEQ01 = 0.0003039874049425295`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
  - sample absolute maxima stay below `0.00038`
- tiny mixed-sign branch deltas do not repair the family's zero negativity score

Why this survives reduction:
- it is the parent batch's clearest metric-versus-objective caution
- later summaries need a compact rule for keeping search failure primary and incidental micro-deltas secondary

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillate `D6`
- parent candidate summary `C4`
- parent tension `T4`
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC4`

Preserved limits:
- this batch does not deny that the micro-deltas are real
- it preserves only that they are weaker than the failed negativity objective

## Quarantined Residue Q1) `SEARCH_BREADTH_AS_SEARCH_SUCCESS`
Status:
- `QUARANTINED`

Preserved residue:
- a large `3456`-record sweep
- all retold as if search width itself proved success

Why it stays quarantined:
- the parent batch explicitly preserves `best.score = 0.0` after full exhaustion
- search breadth is weaker than a successful stored negativity result

Source lineage:
- parent distillate `D2`
- parent candidate summary `C4`
- parent tension `T1`

## Quarantined Residue Q2) `BEST_PLUS_SAMPLE_AS_FULL_SEARCH_TRACE`
Status:
- `QUARANTINED`

Preserved residue:
- one `best` record plus a `10`-record sample
- all treated as if they retained the whole search table

Why it stays quarantined:
- the parent batch explicitly preserves only compressed retained output
- best-plus-sample storage is weaker than full-trace retention

Source lineage:
- parent distillate `D3`
- parent tension `T3`

## Quarantined Residue Q3) `LOCAL_EVIDENCE_AS_REPOTOP_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- catalog presence and local evidence emission
- all treated as if either one promoted the family into repo-top evidence admission

Why it stays quarantined:
- the parent batch explicitly preserves omission of the local `SIM_ID` from the repo-held top-level evidence pack
- local evidence is weaker than repo-top admission

Source lineage:
- parent distillate `D4`
- parent tension `T5`

## Quarantined Residue Q4) `LARGER_STRESS_SWEEP_AS_AUTOMATIC_BASELINE_SUPERSESSOR`
Status:
- `QUARANTINED`

Preserved residue:
- the larger stress sweep
- all treated as if its size alone automatically superseded the smaller baseline

Why it stays quarantined:
- the parent batch explicitly preserves zero best negativity score here and a nonzero negativity tail in the smaller baseline
- search breadth is weaker than stored comparison outcome

Source lineage:
- parent distillate `D6`
- parent candidate summary `C5`
- parent tension `T2`

## Quarantined Residue Q5) `MICRO_BRANCH_DELTAS_AS_COMPENSATION_FOR_ZERO_NEGATIVITY`
Status:
- `QUARANTINED`

Preserved residue:
- tiny mixed-sign branch deltas
- all treated as if they compensated for the family's zero negativity score

Why it stays quarantined:
- the parent batch explicitly preserves only sub-milliscale deltas alongside failed negativity
- micro-deltas are weaker than the search objective they failed to satisfy

Source lineage:
- parent distillate `D6`
- parent candidate summary `C4`
- parent tension `T4`
