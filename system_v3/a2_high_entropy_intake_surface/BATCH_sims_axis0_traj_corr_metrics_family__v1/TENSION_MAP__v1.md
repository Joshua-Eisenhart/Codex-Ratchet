# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_traj_corr_metrics_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_METRICS_PASS`

## T1) The same runner stores nonzero trajectory negativity for Bell init and zero trajectory negativity for Ginibre init
- source markers:
  - `run_axis0_traj_corr_metrics.py:157-212`
  - `results_axis0_traj_corr_metrics.json:1-49`
- tension:
  - Bell stores:
    - `SEQ01.SAgB_neg_frac_traj = 0.09753605769230769`
    - `SEQ02.SAgB_neg_frac_traj = 0.09723557692307692`
  - Ginibre stores:
    - `SEQ01.SAgB_neg_frac_traj = 0.0`
    - `SEQ02.SAgB_neg_frac_traj = 0.0`
- preserved read:
  - initialization regime changes whether the stored trajectory ever enters negative-conditional-entropy territory
- possible downstream consequence:
  - later summaries should keep Bell and Ginibre trajectory-negativity claims separate

## T2) Bell begins with negative conditional entropy, yet both Bell branches end with positive final `SAgB`
- source markers:
  - `results_axis0_traj_corr_metrics.json:2-25`
- tension:
  - Bell initial conditional entropy:
    - `SAgB_init_mean = -0.6931471805599333`
  - Bell final conditional entropy:
    - `SEQ01.SAgB_final_mean = 0.6460960417722438`
    - `SEQ02.SAgB_final_mean = 0.6460646351342514`
- preserved read:
  - the current family stores trajectory negativity without preserving negative final-state conditional entropy
- possible downstream consequence:
  - later summaries should not collapse trajectory negativity into final-state negativity

## T3) Sequence-order deltas are small, but their sign flips across init modes
- source markers:
  - `results_axis0_traj_corr_metrics.json:22-49`
- tension:
  - Bell:
    - `delta_MI_traj_mean_SEQ02_minus_SEQ01 = -0.0004972841850615362`
    - `delta_SAgB_traj_mean_SEQ02_minus_SEQ01 = 0.00047040060007191853`
  - Ginibre:
    - `delta_MI_traj_mean_SEQ02_minus_SEQ01 = 0.00017745381487310752`
    - `delta_SAgB_traj_mean_SEQ02_minus_SEQ01 = -0.00020947935777215765`
- preserved read:
  - there is no init-independent sequence-order direction inside the stored result
- possible downstream consequence:
  - later interpretation should keep branch-order conclusions init-qualified

## T4) Bell carries much larger MI over the trajectory, but Ginibre carries larger positive `SAgB` over the trajectory
- source markers:
  - `results_axis0_traj_corr_metrics.json:2-49`
- tension:
  - Bell:
    - `MI_traj_mean` near `0.199`
    - `SAgB_traj_mean` near `0.459`
  - Ginibre:
    - `MI_traj_mean` near `0.043`
    - `SAgB_traj_mean` near `0.613`
- preserved read:
  - higher stored mutual information does not track with higher stored positive `S(A|B)` trajectory mean in this family
- possible downstream consequence:
  - later summaries should not assume MI and `SAgB` trajectory means move together

## T5) The family is catalog-visible and locally evidenced, but the repo-held top-level evidence pack omits it
- source markers:
  - `SIM_CATALOG_v1.3.md:50`
  - negative search for `axis0_traj_corr_metrics` and `S_SIM_AXIS0_TRAJ_CORR_METRICS` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog lists the family
  - the runner emits a local evidence block
  - the repo-held evidence pack omits the local SIM_ID
- preserved read:
  - keep catalog presence, local evidence, and repo-top admission distinct
- possible downstream consequence:
  - later sims summaries should not mistake local evidence emission for top-level admission

## T6) This family advances the residual paired-family campaign, but the next trajectory-suite pair still stays out of batch
- source markers:
  - `BATCH_sims_axis0_sagb_entangle_seed_family__v1/MANIFEST.json`
  - residual folder order placing `run_axis0_traj_corr_suite.py` after `run_axis0_traj_corr_metrics.py`
- tension:
  - the paired-family campaign continues cleanly
  - the next adjacent suite family is clearly related by name but remains a separate bounded pair
- preserved read:
  - keep the metrics family separate from the suite family
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis0_traj_corr_suite.py`
