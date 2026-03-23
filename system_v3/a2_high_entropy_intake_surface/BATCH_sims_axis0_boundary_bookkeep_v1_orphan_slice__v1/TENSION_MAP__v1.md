# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
Extraction mode: `SIM_AXIS0_BOUNDARY_BOOKKEEP_V1_ORPHAN_SLICE_PASS`

## T1) The current surface is a result-only orphan, but it is an exact overlapping-metric slice of the already-batched boundary/bookkeep sweep family
- source markers:
  - `results_axis0_boundary_bookkeep_v1.json:1-82`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:1-174`
  - `BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
- tension:
  - current orphan stands alone in source membership
  - overlapping mean metrics match the sweep family exactly at:
    - `sign1_BELL_REC1`
    - `sign1_GINIBRE_REC1`
    - `SEQ01`
    - `SEQ02`
- preserved read:
  - keep the orphan bounded to one file while preserving its exact linkage to the sweep family
- possible downstream consequence:
  - later summaries should not describe this orphan as disconnected from the already-batched boundary/bookkeeping family

## T2) The current orphan is derivative of the sweep family, but it is not a redundant duplicate because it stores extra extrema and zero-negativity fields
- source markers:
  - `results_axis0_boundary_bookkeep_v1.json:1-82`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:1-174`
- tension:
  - shared mean metrics match exactly
  - current orphan adds:
    - `dMI_max`
    - `dMI_min`
    - `dSAgB_max`
    - `dSAgB_min`
    - `frob_err_max`
    - `frob_err_min`
    - `neg_SAgB_frac_bulk`
    - `neg_SAgB_frac_rec`
- preserved read:
  - current surface is a compact enriched slice, not just a renamed extract
- possible downstream consequence:
  - later summaries should preserve both the duplication of the core means and the local enrichment of the orphan

## T3) BELL carries much larger bookkeeping displacement than GINIBRE, while all stored negativity remains zero
- source markers:
  - `results_axis0_boundary_bookkeep_v1.json:1-82`
- tension:
  - strongest absolute `dMI_mean`:
    - `BELL_SEQ02 = -0.025370200134149742`
  - weakest absolute `dMI_mean`:
    - `GINIBRE_SEQ01 = -0.005445352215660112`
  - all `neg_SAgB_frac_bulk` and `neg_SAgB_frac_rec` values are `0.0`
- preserved read:
  - the orphan carries a strong init-class separation without any stored negativity signal
- possible downstream consequence:
  - later summaries should not conflate large bookkeeping displacement with negativity production

## T4) `results_axis0_traj_corr_suite_v2.json` is catalog-adjacent, but it stays separate because its lattice and metric contract are fundamentally different
- source markers:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- tension:
  - current orphan:
    - `4` payloads
    - `2` sequences
    - one sign
    - bookkeeping metrics
  - deferred trajectory orphan:
    - `128` entries
    - `4` sequences
    - `32` baseline prefixes
    - `96` delta entries
    - trajectory metrics like `Lam_MI_decay_fit`, `MI_traj_mean`, `dLam`, `dNegFrac`
- preserved read:
  - catalog adjacency does not license a shared bounded family here
- possible downstream consequence:
  - later summaries should process `traj_corr_suite_v2` separately rather than merging it into this bookkeeping slice

## T5) Both current and deferred axis0 orphans are catalog-visible by filename alias only, while the evidence pack omits them entirely
- source markers:
  - `SIM_CATALOG_v1.3.md:42-43,51-52`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - catalog visibility:
    - yes
  - evidence-pack filename or family-name visibility:
    - no
- preserved read:
  - keep catalog listing separate from evidence admission
- possible downstream consequence:
  - later summaries should not mistake catalog presence for proof of a maintained evidence surface

## T6) The current orphan has no direct runner-name hit in `simpy/`, but it still has a better source anchor than the deferred trajectory orphan because the sweep-family overlap is exact
- source markers:
  - file inventory search across `simpy/`
  - current orphan and sweep-family comparison
- tension:
  - no direct runner file names are recoverable for the current orphan
  - despite that, the current orphan has exact metric overlap with an already-batched family
  - the deferred trajectory orphan currently has neither a direct runner-name hit nor an exact family slice anchor
- preserved read:
  - source-anchor quality is stronger for the current orphan than for the adjacent deferred orphan
- possible downstream consequence:
  - later summaries should keep the anchor-quality asymmetry explicit when sequencing the remaining result-only residual work
