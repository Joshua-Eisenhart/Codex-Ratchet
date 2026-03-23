# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_ultra_big_ax012346_orphan_family__v1`
Extraction mode: `SIM_ULTRA_BIG_AX012346_ORPHAN_PASS`

## T1) The local ultra-big surface exists in the catalog, but the repo-held top-level evidence pack omits it and no direct runner-name hit is recoverable
- source markers:
  - `results_ultra_big_ax012346.json:1-305`
  - `SIM_CATALOG_v1.3.md:118`
  - negative search for `ultra_big` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - negative search for `ultra_big` in current `simpy/`
- tension:
  - the file is catalog-visible
  - the repo-held evidence pack contains no matching block
  - no direct runner is recoverable from current `simpy/`
- preserved read:
  - keep catalog presence distinct from evidence admission and executable provenance
- possible downstream consequence:
  - this batch should stay proposal-side in provenance strength

## T2) The file declares `entangle_reps = 2`, but `ent0` and `ent1` are invariant to machine precision
- source markers:
  - `results_ultra_big_ax012346.json:1-305`
- tension:
  - metadata exposes a repeat axis
  - max absolute metric difference across ent0 and ent1 is only:
    - `3.469446951953614e-17` for `sign-1`
    - `1.1102230246251565e-16` for `sign1`
- preserved read:
  - do not overstate the stored importance of the entanglement-repeat axis
- possible downstream consequence:
  - later reads should treat ent-repeat here as a nearly inert label unless a runner source proves otherwise

## T3) The sign effect is real, but much smaller than the stored sequence effect
- source markers:
  - `results_ultra_big_ax012346.json:1-305`
- tension:
  - for `SEQ02 / BELL`, `sign1 - sign-1` is only:
    - `dMI_mean = 3.584325813296707e-05`
    - `dSAgB_mean = -0.0005204740469357816`
    - `dnegfrac_mean = 0.0`
  - for `sign1 / BELL`, `SEQ02 - SEQ01` is:
    - `dMI_mean = 0.002251349097335875`
    - `dSAgB_mean = -0.0027451465467724923`
    - `dnegfrac_mean = 0.001953125`
- preserved read:
  - keep the sign seam, but preserve that sequence dominates it numerically
- possible downstream consequence:
  - later summaries should avoid centering sign as the main explanatory axis for this source

## T4) Bell carries persistent negativity while Ginibre stays zero-negative throughout
- source markers:
  - `results_ultra_big_ax012346.json:1-305`
- tension:
  - Bell `negfrac_mean` is nonzero for both stored sequences
  - Ginibre `negfrac_mean` remains `0.0` across all stored branches
- preserved read:
  - the init split is durable even though ent-repeat is not
- possible downstream consequence:
  - later trajectory readings should preserve Bell vs Ginibre as a stronger seam than ent-repeat

## T5) The topology4 branch contains two different splits at once: adaptive vs fixed and EC vs EO
- source markers:
  - `results_ultra_big_ax012346.json:1-305`
- tension:
  - adaptive families carry the only nontrivial `lin_err_mean`
  - fixed families are effectively linear
  - EC commuting-control deltaH is near zero
  - EO commuting-control deltaH remains materially nonzero
- preserved read:
  - do not flatten topology4 into one homogeneous summary layer
- possible downstream consequence:
  - later topology synthesis should preserve both orthogonal splits rather than just adaptive-vs-fixed

## T6) Ultra-big is an ultra orphan, but not the same bounded family as the prior ultra3 orphan
- source markers:
  - `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1/MANIFEST.json`
  - `results_ultra_big_ax012346.json:1-305`
- tension:
  - ultra3 has:
    - berry flux
    - `stage16`
    - `128` `axis0_ab` entries
    - `4` sequences
  - current orphan has:
    - topology4 metrics
    - `axis0_traj_metrics`
    - `2` sequences
    - no berry flux
    - no `stage16`
- preserved read:
  - the current orphan closes the result-only ultra strip without merging back into ultra3
- possible downstream consequence:
  - the next residual pass should leave result-only work entirely and begin the diagnostic/proof residue
