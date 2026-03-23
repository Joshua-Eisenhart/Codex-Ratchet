# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_axis0_mutualinfo_killgate_boundary__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `AXIS0_MUTUALINFO_BASELINE_PAIR_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_axis0_mutual_info.py` and `results_axis0_mutual_info.json` should stay compressed as:
  - one standalone mutual-information baseline residual paired family
  - one runner plus one paired result
  - one bounded family rather than one loose residual file or one merged baseline-plus-stress negativity block

Why this survives reduction:
- it is the parent batch's cleanest family-shell claim
- it preserves the baseline pair as its own reusable unit inside the residual lane

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidate summaries:
  - `C1`
  - `C2`
- comparison anchor:
  - `BATCH_A2MID_axis0_ab_mi_revival__v1:RC1`

Preserved limits:
- this batch does not absorb the adjacent stress sweep
- it preserves only the current baseline pair as one bounded family

## Candidate RC2) `KILL_GATE_VS_STORED_NEGATIVITY_ESCAPE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest executable-to-result seam in the parent batch is:
  - the runner writes a kill token only if `neg_SAgB_frac == 0.0`
  - the stored output does not trigger that path
  - it escapes only by the thinnest possible margin:
    - `neg_SAgB_frac = 0.001953125`
    - one negative event in `512` trials

Why this survives reduction:
- it is the parent batch's clearest success-versus-gate packet
- later summaries need a compact rule for describing this family as barely clearing its own local criterion

Source lineage:
- parent clusters:
  - `A`
  - `B`
- parent distillates:
  - `D2`
  - `D3`
- parent candidate summary `C3`
- parent tension `T1`

Preserved limits:
- this batch does not claim the family strongly passes a harder negativity bar
- it preserves only that the stored result is on the surviving side of the local gate

## Candidate RC3) `LOCAL_BASELINE_EVIDENCE_WITHOUT_REPOTOP_ADMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest evidence-status packet in the parent batch is:
  - the runner emits one explicit local `SIM_EVIDENCE` block
  - the catalog lists the family
  - the repo-held top-level evidence pack contains neither the local `SIM_ID` nor the kill token
- local evidence emission and kill-gate logic must stay weaker than repo-top admission

Why this survives reduction:
- it is the parent batch's main visibility contradiction
- later residual summaries need the baseline kept source-real and locally evidenced without overstating its top-level admission status

Source lineage:
- parent cluster `D`
- parent distillate `D4`
- parent tension `T2`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC3`

Preserved limits:
- this batch does not deny the local evidence contract
- it preserves only that local evidence, local kill logic, and repo-top admission are not the same layer

## Candidate RC4) `POSITIVE_MI_WITH_TINY_NEGATIVITY_TAIL_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the baseline family should preserve one compact metric packet:
  - `MI` is robustly positive across its stored summary statistics
  - the negativity evidence is only a tiny tail:
    - `neg_SAgB_frac = 0.001953125`
    - `SAgB_min = -0.002114071978150056`
- positive `MI` is not the same as strong negativity success

Why this survives reduction:
- it is the parent batch's clearest anti-collapse packet between the MI baseline and the fragility of the negativity claim
- later summaries need a compact rule for not promoting the small negativity tail into a robust success story

Source lineage:
- parent cluster `B`
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C4`
- parent tension `T4`

Preserved limits:
- this batch does not deny that the negativity tail is real
- it preserves only that it is much weaker than the positive MI layer

## Candidate RC5) `BASELINE_OVER_STRESS_SWEEP_NEGATIVITY_INVERSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the comparison to `negsagb_stress` should keep one inversion packet:
  - the smaller baseline stores a tiny nonzero negativity fraction
  - the larger adjacent stress sweep stores best negativity score `0.0`
- the larger search family does not automatically dominate the smaller baseline

Why this survives reduction:
- it is the parent batch's clearest anti-supersession packet
- later backlog work needs a compact rule for preserving this inversion before entering the search family

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D5`
  - `D6`
- parent candidate summary `C5`
- parent tension `T3`

Preserved limits:
- this batch does not deny that the stress family is broader or next in queue
- it preserves only that breadth does not automatically beat the stored baseline result

## Candidate RC6) `COMPACT_BASELINE_GRANULARITY_LIMIT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the compact baseline result surface should stay weaker than rich dynamic interpretation because:
  - the runner iterates over `512` trials
  - the stored output keeps only aggregate means, extrema, and one negativity fraction
- compact baseline summaries are not the same as trial-level structure

Why this survives reduction:
- it is the parent batch's clearest granularity caution packet
- later reductions need a compact rule for not over-claiming structure beyond the stored summary level

Source lineage:
- parent cluster `B`
- parent distillate `D6`
- parent tension `T5`
- comparison anchor:
  - `BATCH_A2MID_axis0_nonab_sagb_vs_mi__v1:RC6`

Preserved limits:
- this batch does not deny that the compact surface is useful
- it preserves only that summary granularity is weaker than full trial-level diagnostics

## Quarantined Residue Q1) `KILL_GATE_PRESENCE_AS_KILL_TRIGGER`
Status:
- `QUARANTINED`

Preserved residue:
- the runner contains a kill gate
- all retold as if the stored output therefore triggered it

Why it stays quarantined:
- the parent batch explicitly preserves a nonzero stored negativity fraction
- gate presence is weaker than gate triggering

Source lineage:
- parent distillate `D3`
- parent tension `T1`

## Quarantined Residue Q2) `LOCAL_EVIDENCE_OR_KILL_TOKEN_AS_REPOTOP_ADMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- local evidence emission
- local kill-gate logic
- all treated as if either one promoted the family into repo-top evidence admission

Why it stays quarantined:
- the parent batch explicitly preserves no repo-top evidence-pack match for the local `SIM_ID` or kill token
- local artifacts are weaker than repo-top admission

Source lineage:
- parent distillate `D4`
- parent tension `T2`

## Quarantined Residue Q3) `POSITIVE_MI_AS_ROBUST_NEGATIVITY`
Status:
- `QUARANTINED`

Preserved residue:
- robustly positive stored `MI`
- all retold as if that alone proved a strong negativity result

Why it stays quarantined:
- the parent batch explicitly preserves only a one-in-512 negativity tail
- positive `MI` is weaker than robust negativity success

Source lineage:
- parent distillates:
  - `D2`
  - `D6`
- parent candidate summary `C4`
- parent tension `T4`

## Quarantined Residue Q4) `STRESS_SWEEP_AS_AUTOMATIC_BASELINE_SUPERSESSOR`
Status:
- `QUARANTINED`

Preserved residue:
- the larger adjacent stress sweep
- all treated as if its size alone automatically superseded the smaller baseline

Why it stays quarantined:
- the parent batch explicitly preserves best stress negativity score `0.0` while the smaller baseline stores a tiny nonzero tail
- search breadth is weaker than stored outcome

Source lineage:
- parent distillate `D5`
- parent candidate summary `C5`
- parent tension `T3`

## Quarantined Residue Q5) `COMPACT_BASELINE_SUMMARY_AS_TRIAL_LEVEL_PROOF`
Status:
- `QUARANTINED`

Preserved residue:
- compact means, extrema, and one negativity fraction
- all treated as if they fully proved the family’s trial-level structure

Why it stays quarantined:
- the parent batch explicitly preserves only summary-level evidence
- compact summaries are weaker than trial-level proof

Source lineage:
- parent distillate `D6`
- parent tension `T5`
