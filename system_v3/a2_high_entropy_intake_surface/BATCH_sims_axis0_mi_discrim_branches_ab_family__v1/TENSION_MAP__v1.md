# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_AB_PASS`

## T1) The runner frames AB coupling as "the fix", but the repo-held top-level evidence pack still omits the family
- source markers:
  - `run_axis0_mi_discrim_branches_ab.py:146`
  - `run_axis0_mi_discrim_branches_ab.py:211-232`
  - negative search for `axis0_mi_discrim_branches_ab` and `S_SIM_AXIS0_MI_DISCRIM_BRANCHES_AB` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_CATALOG_v1.3.md:46`
- tension:
  - the runner explicitly labels the CNOT insertion as `the fix`
  - the runner writes one local evidence block for `S_SIM_AXIS0_MI_DISCRIM_BRANCHES_AB`
  - the repo-held evidence pack still contains no matching block
- preserved read:
  - keep local corrective framing distinct from repo-top admission
- possible downstream consequence:
  - later sims summaries should treat this family as source-real but not top-level evidenced

## T2) AB coupling revives a real MI branch split, but negativity still does not appear
- source markers:
  - `results_axis0_mi_discrim_branches_ab.json:1-49`
- tension:
  - `metrics_SEQ01.MI_mean = 0.005174869538448677`
  - `metrics_SEQ02.MI_mean = 0.005913066231490261`
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 0.0007381966930415842`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
- preserved read:
  - the current family turns on MI signal without producing any stored negative conditional-entropy fraction
- possible downstream consequence:
  - later interpretation should not equate nonzero MI with negativity onset in this family

## T3) The AB family is a true successor to the non-AB sibling, but the metric shift is not one-dimensional
- source markers:
  - `results_axis0_mi_discrim_branches_ab.json:1-49`
  - `results_axis0_mi_discrim_branches.json:1-48`
- tension:
  - relative to non-AB, the current AB family:
    - raises `SEQ01.MI_mean` by `0.005174869538448698`
    - raises `SEQ02.MI_mean` by `0.005913066231490281`
    - raises `delta_MI_mean_SEQ02_minus_SEQ01` by `0.0007381966930415822`
  - but it also reduces the absolute `SAgB` branch split by `0.0013528798520251462`
- preserved read:
  - AB coupling does not simply increase every branch-discriminator metric at once
- possible downstream consequence:
  - later summaries should preserve MI gain and `SAgB` attenuation as separate effects

## T4) The family is named as an MI discriminator and now does earn that label, but only under the added CNOT contract
- source markers:
  - `run_axis0_mi_discrim_branches_ab.py:131-154`
  - `run_axis0_mi_discrim_branches.py:116-139`
  - both paired result surfaces
- tension:
  - the non-AB sibling kept MI at machine-zero scale
  - the AB family earns a real MI split only because the executable contract changed
- preserved read:
  - the label becomes more faithful here, but only relative to the prior control sibling
- possible downstream consequence:
  - later backlog work should describe the current family as the AB-coupled discriminator rather than back-projecting its signal onto the non-AB family

## T5) Compact result formatting still compresses the family to branch-level means and hides trajectory structure
- source markers:
  - `results_axis0_mi_discrim_branches_ab.json:1-49`
  - `run_axis0_mi_discrim_branches_ab.py:175-232`
- tension:
  - the current result surface stores only compact branch summaries
  - the evidence block foregrounds top-level means and deltas rather than richer within-run structure
- preserved read:
  - keep compact evidence formatting distinct from full dynamic interpretation
- possible downstream consequence:
  - later summaries should avoid over-claiming dynamics that are not stored in the current surface

## T6) This family advances the residual paired-family campaign, but the remaining residual classes are still separate
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `BATCH_sims_axis0_mi_discrim_branches_family__v1/MANIFEST.json`
- tension:
  - the paired-family campaign is advancing cleanly
  - result-only, runner-only, diagnostic, and hygiene residual classes remain outside this campaign
- preserved read:
  - keep paired-family intake separate from the other residual classes
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis0_mutual_info.py`
