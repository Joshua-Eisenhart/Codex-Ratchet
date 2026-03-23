# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_sagb_entangle_seed_family__v1`
Extraction mode: `SIM_AXIS0_SAGB_ENTANGLE_SEED_PASS`

## T1) The runner injects randomized local scrambles into every Bell seed, but the stored branch metrics are effectively deterministic
- source markers:
  - `run_axis0_sagb_entangle_seed.py:114-126`
  - `results_axis0_sagb_entangle_seed.json:1-50`
- tension:
  - each trial starts from a Bell seed with random local-unitary scramble
  - the stored per-branch ranges collapse to floating-point noise:
    - branch MI ranges `= 2.6645352591003757e-15`
    - branch `SAgB` ranges `~ 2.5e-15`
- preserved read:
  - keep randomized initialization distinct from meaningful trial-level dispersion
- possible downstream consequence:
  - later summaries should describe the current family as effectively deterministic at stored precision

## T2) The family uses Bell seeds, weak noise, and repeated CNOT coupling, yet stored negativity stays at zero
- source markers:
  - `run_axis0_sagb_entangle_seed.py:167-230`
  - `results_axis0_sagb_entangle_seed.json:1-50`
- tension:
  - the family seems engineered to keep entanglement alive:
    - Bell seed
    - weak noise `0.005`
    - `2` CNOT repetitions per terrain step
  - both branches still store:
    - `neg_SAgB_frac = 0.0`
- preserved read:
  - strong entangling setup does not automatically imply negative conditional entropy in storage
- possible downstream consequence:
  - later summaries should not project negativity onto this family just from its setup

## T3) The family preserves tiny branch differences without any stored negativity event
- source markers:
  - `results_axis0_sagb_entangle_seed.json:1-50`
- tension:
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 9.72232227303138e-06`
  - `delta_SAgB_min_SEQ02_minus_SEQ01 = -2.675544964136911e-05`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- preserved read:
  - the current family stores small branch discrimination in positive-`SAgB` space rather than negativity space
- possible downstream consequence:
  - later interpretation should separate branch discrimination from negativity success

## T4) The current fixed Bell-seed family and the prior negativity-stress sweep converge on the same stored nonnegativity outcome for different reasons
- source markers:
  - `results_axis0_sagb_entangle_seed.json:1-50`
  - `results_axis0_negsagb_stress.json:1-380`
- tension:
  - the prior stress family failed to find any positive negativity score across `3456` searched settings
  - the current family is not a search failure surface; it is one fixed contract that also stores zero negativity
- preserved read:
  - keep search failure distinct from fixed-contract nonnegativity
- possible downstream consequence:
  - later summaries should not blur these two zero-negativity families into one type of failure

## T5) The family is catalog-visible and locally evidenced, but the repo-held top-level evidence pack omits it
- source markers:
  - `SIM_CATALOG_v1.3.md:49`
  - negative search for `axis0_sagb_entangle_seed` and `S_SIM_AXIS0_SAGB_ENTANGLE_SEED` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog lists the family
  - the runner emits a local evidence block
  - the repo-held evidence pack omits the local SIM_ID
- preserved read:
  - keep catalog presence, local evidence, and repo-top admission distinct
- possible downstream consequence:
  - later sims summaries should not mistake local evidence emission for top-level admission

## T6) This family advances the residual paired-family campaign, but the remaining residual classes stay separate
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `BATCH_sims_axis0_negsagb_stress_family__v1/MANIFEST.json`
- tension:
  - the paired-family campaign is advancing cleanly
  - result-only, runner-only, diagnostic, and hygiene residual classes remain outside this campaign
- preserved read:
  - keep paired-family intake separate from the other residual classes
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis0_traj_corr_metrics.py`
