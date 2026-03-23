# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_axis0_mi_discrim_branches_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_PASS`

## Cluster A
- cluster label:
  - core source pair
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one runner
  - one paired result
  - one local SIM_ID
- tension anchor:
  - the family is locally complete as a runner/result pair but its stored MI discriminator is effectively zero

## Cluster B
- cluster label:
  - compact branch-metric contract
- members:
  - `metrics_SEQ01`
  - `metrics_SEQ02`
  - `delta_MI_mean_SEQ02_minus_SEQ01`
  - `delta_SAgB_mean_SEQ02_minus_SEQ01`
- family role:
  - internal metric cluster carried by the one stored result surface
- executable-facing read:
  - both branches keep `neg_SAgB_frac = 0.0`
  - branch discrimination appears in `SAgB`
  - branch discrimination does not appear materially in stored MI
- tension anchor:
  - the file name foregrounds MI, but the stored split is in a different metric layer

## Cluster C
- cluster label:
  - `_ab` sibling next-family anchor
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches_ab.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mi_discrim_branches_ab.json`
- family role:
  - comparison-only sibling cluster for boundary setting
- executable-facing read:
  - adds explicit AB coupling through `CNOT`
  - yields nonzero MI means and a nonzero MI delta
- tension anchor:
  - nominal family proximity does not justify merging the non-AB and AB variants

## Cluster D
- cluster label:
  - top-level visibility and backlog continuity
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_historyop_rec_suite_v1_family__v1/MANIFEST.json`
- family role:
  - comparison-only visibility and campaign-continuity cluster
- executable-facing read:
  - catalog lists current and sibling families
  - evidence pack omits current local SIM_ID
  - prior residual batch points here as the next pair
- tension anchor:
  - catalog presence, local evidence, and repo-top admission do not align

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B explains why the current family is more of an `SAgB` discriminator than an MI discriminator
- Cluster C justifies the batch boundary against the adjacent `_ab` sibling
- Cluster D preserves visibility and campaign continuity without broadening the batch
