# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_traj_corr_suite_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_PASS`

## T1) The local suite SIM_ID is omitted from the repo-held top-level evidence pack, but the pack admits `V4` and `V5` descendants under the same code hash
- source markers:
  - `run_axis0_traj_corr_suite.py:236-263`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:1-26`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json:1-17`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json:1-26`
- tension:
  - the current runner emits local evidence for `S_SIM_AXIS0_TRAJ_CORR_SUITE`
  - the repo-held evidence pack omits that SIM_ID
  - the repo-held evidence pack instead admits:
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V4`
    - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V5`
  - both descendant evidence blocks carry the current runner hash `a42e220706a47d27283a332980398c35035e81efc7c188896ad388e5de5961bb`
- preserved read:
  - keep code-hash continuity distinct from SIM_ID continuity
- possible downstream consequence:
  - later summaries should not treat the local suite as repo-top admitted just because descendants share its code hash

## T2) The runner stores a full 32-case lattice, but its evidence block emits only `SEQ01`-relative deltas
- source markers:
  - `run_axis0_traj_corr_suite.py:238-263`
  - `results_axis0_traj_corr_suite.json:1-364`
- tension:
  - the result surface stores every case explicitly
  - the evidence block compresses each sign/init/direction slice to three delta comparisons against `SEQ01`
- preserved read:
  - the local evidence block is a compressed summary, not the full data surface
- possible downstream consequence:
  - later summaries should not reconstruct the full lattice from the delta-only evidence block alone

## T3) `SEQ04` flips from suppressed Bell behavior in `FWD` to the strongest Bell anomaly in `REV`
- source markers:
  - `results_axis0_traj_corr_suite.json:170-249`
- tension:
  - `sign1_BELL_FWD_SEQ04` stores:
    - `MI_traj_mean = 0.1470168871279225`
    - `SAgB_neg_frac_traj = 0.06995192307692308`
    - `SAgB_traj_mean = 0.5110568647917657`
  - `sign1_BELL_REV_SEQ04` stores:
    - `MI_traj_mean = 0.29728021483432243`
    - `SAgB_neg_frac_traj = 0.1373798076923077`
    - `SAgB_traj_mean = 0.358440136696848`
- preserved read:
  - `SEQ04` is direction-sensitive rather than uniformly weak or uniformly strong
- possible downstream consequence:
  - later summaries should keep direction attached to any claim about `SEQ04`

## T4) Bell keeps nonzero trajectory negativity across the whole suite, while Ginibre keeps it at zero across the whole suite
- source markers:
  - `results_axis0_traj_corr_suite.json:10-329`
- tension:
  - Bell cases store nonzero `SAgB_neg_frac_traj` throughout the suite
  - Ginibre cases store `SAgB_neg_frac_traj = 0.0` throughout the suite
- preserved read:
  - the init-regime split remains absolute at the stored trajectory-negativity level
- possible downstream consequence:
  - later summaries should not blur Bell and Ginibre into one averaged negativity story

## T5) Axis3 sign reversal is close to symmetric, but not exact
- source markers:
  - `results_axis0_traj_corr_suite.json:10-329`
- tension:
  - example pair `sign1_BELL_FWD_SEQ01` vs `sign-1_BELL_FWD_SEQ01` differs by:
    - `delta_MI_traj_mean = -0.0008544227584726116`
    - `delta_SAgB_traj_mean = 0.0008886054822548339`
    - `delta_SAgB_neg_frac_traj = -0.00324519230769231`
  - example pair `sign1_BELL_REV_SEQ04` vs `sign-1_BELL_REV_SEQ04` differs by:
    - `delta_MI_traj_mean = 0.00012148923412569346`
    - `delta_SAgB_traj_mean = -0.0001398879898606431`
    - `delta_SAgB_neg_frac_traj = -0.004447115384615369`
- preserved read:
  - sign reversal looks nearly symmetric but still leaves stored nonzero residuals
- possible downstream consequence:
  - later summaries should avoid overstating exact sign symmetry

## T6) The local suite is catalog-visible and locally evidenced, but the residual campaign still moves on to axis12 instead of merging families
- source markers:
  - `SIM_CATALOG_v1.3.md:51-52`
  - `BATCH_sims_axis0_traj_corr_metrics_family__v1/MANIFEST.json`
  - raw folder order placing `run_axis12_channel_realization_suite.py` after `run_axis0_traj_corr_suite.py`
- tension:
  - the current axis0 suite is locally complete and catalog-visible
  - the campaign still treats the next axis12 pair as a separate bounded family
- preserved read:
  - keep adjacent residual pairs separate even when both are suite-shaped surfaces
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis12_channel_realization_suite.py`
