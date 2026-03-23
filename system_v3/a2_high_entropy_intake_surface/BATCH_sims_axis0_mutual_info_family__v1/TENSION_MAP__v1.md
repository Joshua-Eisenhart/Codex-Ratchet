# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_mutual_info_family__v1`
Extraction mode: `SIM_AXIS0_MUTUAL_INFO_PASS`

## T1) The runner contains a kill gate for zero negativity, but the stored output escapes it by the thinnest possible margin
- source markers:
  - `run_axis0_mutual_info.py:115-133`
  - `results_axis0_mutual_info.json:1-15`
- tension:
  - the runner writes `KILL_SIGNAL S_AXIS0_CAND_MI_V1 CORR AX0MI_FAIL` only if `neg_SAgB_frac == 0.0`
  - the stored output has:
    - `neg_SAgB_frac = 0.001953125`
    - `SAgB_min = -0.002114071978150056`
  - `0.001953125` corresponds to one negative event in `512` trials
- preserved read:
  - keep kill-gate logic distinct from the currently stored outcome
- possible downstream consequence:
  - later summaries should describe this family as barely clearing its own local kill criterion rather than strongly establishing negativity

## T2) The family is catalog-visible and locally evidenced, but the repo-held top-level evidence pack omits it
- source markers:
  - `SIM_CATALOG_v1.3.md:47`
  - negative search for `axis0_mutual_info`, `S_SIM_AXIS0_MI_TEST`, `S_AXIS0_CAND_MI_V1`, and `AX0MI_FAIL` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog lists the mutual-info family
  - the runner emits a local evidence block
  - the repo-held top-level pack includes neither the local SIM_ID nor the kill token
- preserved read:
  - keep catalog presence, local evidence, and repo-top admission distinct
- possible downstream consequence:
  - later sims summaries should not mistake local evidence emission for top-level admission

## T3) The minimal baseline produces a tiny negativity tail, but the adjacent stress sweep stores a best score of zero
- source markers:
  - `results_axis0_mutual_info.json:1-15`
  - `results_axis0_negsagb_stress.json:1-220`
- tension:
  - the current baseline stores:
    - `neg_SAgB_frac = 0.001953125`
  - the larger adjacent stress sweep stores:
    - `best.score = 0.0`
    - `best.rec.SEQ01.neg_SAgB_frac = 0.0`
    - `best.rec.SEQ02.neg_SAgB_frac = 0.0`
- preserved read:
  - the larger search family does not automatically dominate the smaller baseline family
- possible downstream consequence:
  - later backlog work should preserve this inversion rather than assuming the stress sweep supersedes the baseline

## T4) The family is called mutual-information, but its most fragile evidence claim is actually the negativity tail
- source markers:
  - `results_axis0_mutual_info.json:1-15`
- tension:
  - stored MI is robustly positive:
    - `MI_mean = 0.2724236385732822`
    - `MI_min = 0.07228029839730787`
    - `MI_max = 0.5763919004845633`
  - the decisive local gate in the runner is instead tied to negativity:
    - `neg_SAgB_frac`
- preserved read:
  - keep the MI baseline layer distinct from the family’s local success/failure gate
- possible downstream consequence:
  - later summaries should not collapse positive MI into proof of the stronger negativity-oriented claim

## T5) The result surface is extremely compact and hides all trial-level structure
- source markers:
  - `run_axis0_mutual_info.py:61-114`
  - `results_axis0_mutual_info.json:1-15`
- tension:
  - the runner iterates over `512` trials
  - the stored output keeps only aggregate means, extrema, and one negativity fraction
- preserved read:
  - compact evidence formatting is not the same as high-resolution diagnostic structure
- possible downstream consequence:
  - later interpretation should stay within the stored summary granularity

## T6) This family advances the residual paired-family campaign, but the remaining residual classes stay separate
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1/MANIFEST.json`
- tension:
  - the paired-family campaign is advancing cleanly
  - result-only, runner-only, diagnostic, and hygiene residual classes remain outside this campaign
- preserved read:
  - keep paired-family intake separate from the other residual classes
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis0_negsagb_stress.py`
