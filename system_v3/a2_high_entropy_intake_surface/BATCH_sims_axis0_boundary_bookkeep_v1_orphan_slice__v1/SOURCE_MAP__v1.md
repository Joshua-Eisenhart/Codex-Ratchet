# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
Extraction mode: `SIM_AXIS0_BOUNDARY_BOOKKEEP_V1_ORPHAN_SLICE_PASS`
Batch scope: residual result-only axis0 boundary/bookkeeping orphan centered on `results_axis0_boundary_bookkeep_v1.json`, with the earlier boundary-bookkeep sweep and the adjacent `results_axis0_traj_corr_suite_v2.json` preserved comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_v1.json`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_v1.json`
- reason for bounded family:
  - this is the next remaining result-only orphan after the harden-strip `v1` and `v2` triplets
  - repo-local comparison shows it is an exact overlapping-metric slice of the already-batched boundary-bookkeep sweep family rather than part of the adjacent trajectory-correlation orphan
  - `results_axis0_traj_corr_suite_v2.json` stays separate because it uses a different lattice, different metric contract, different sequence coverage, and no shared source anchor
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_sweep_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`

## 2) Source Membership
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_v1.json`
  - sha256: `cee89ed9ad0eb5d1acd9a1e5aaaa192f74be1f9452c5d2032fafaec4b99ebd00`
  - size bytes: `2130`
  - line count: `82`
  - source role: compact sign1/REC1 axis0 boundary/bookkeeping slice across BELL and GINIBRE initializations for `SEQ01` and `SEQ02`

## 3) Structural Map Of The Family
### Result structure: `results_axis0_boundary_bookkeep_v1.json`
- anchors:
  - `results_axis0_boundary_bookkeep_v1.json:1-82`
- source role:
  - compact boundary/bookkeeping surface with:
    - `4` init/sequence payloads:
      - `BELL_SEQ01`
      - `BELL_SEQ02`
      - `GINIBRE_SEQ01`
      - `GINIBRE_SEQ02`
    - `2` stored sequence definitions:
      - `SEQ01`
      - `SEQ02`
    - one fixed control setting:
      - `axis3_sign = 1`
      - `trials = 512`
      - `cycles = 64`
      - `entangle_reps = 1`
      - `record_axis = Z`
      - `terrain_params = {gamma: 0.01, p: 0.01, q: 0.01}`
- strongest bounded reads:
  - BELL carries the strongest bookkeeping deltas:
    - `BELL_SEQ02 dMI_mean = -0.025370200134149742`
    - `BELL_SEQ02 dSAgB_mean = 0.025370200134149735`
    - `BELL_SEQ02 frob_err_mean = 0.12464570444345227`
  - GINIBRE is materially weaker:
    - weakest absolute `dMI_mean` is `GINIBRE_SEQ01 = -0.005445352215660112`
  - all stored negativity fractions are zero:
    - `neg_SAgB_frac_bulk = 0.0`
    - `neg_SAgB_frac_rec = 0.0`
- bounded implication:
  - the orphan surface is a compact bookkeeping slice with strong BELL-vs-GINIBRE separation and no stored negativity

### Exact overlap relation to `results_axis0_boundary_bookkeep_sweep_v2.json`
- comparison anchors:
  - `results_axis0_boundary_bookkeep_sweep_v2.json:1-174`
  - `BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
- bounded read:
  - all overlapping mean metrics are exact matches to the `sign1_*_REC1` slice of the already-batched sweep family:
    - `BELL_SEQ01` == `sign1_BELL_REC1 / SEQ01`
    - `BELL_SEQ02` == `sign1_BELL_REC1 / SEQ02`
    - `GINIBRE_SEQ01` == `sign1_GINIBRE_REC1 / SEQ01`
    - `GINIBRE_SEQ02` == `sign1_GINIBRE_REC1 / SEQ02`
  - the current orphan surface also stores extra fields absent from the sweep slice:
    - `dMI_max`
    - `dMI_min`
    - `dSAgB_max`
    - `dSAgB_min`
    - `frob_err_max`
    - `frob_err_min`
    - `neg_SAgB_frac_bulk`
    - `neg_SAgB_frac_rec`
- bounded implication:
  - the orphan is not an unrelated result; it is a compact, enriched slice of the boundary-bookkeep family already anchored by the sweep batch

### Separation from `results_axis0_traj_corr_suite_v2.json`
- comparison anchors:
  - `results_axis0_traj_corr_suite_v2.json:1-939`
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
- bounded read:
  - the adjacent orphan uses a different top-level contract:
    - current orphan:
      - `4` init/sequence payloads
      - `2` sequences
      - one sign
      - bookkeeping metrics and reconstruction error summaries
    - `traj_corr_suite_v2`:
      - `128` axis0-traj entries
      - `4` sequences
      - `32` baseline prefixes and `96` delta entries
      - directions `FWD` / `REV`
      - gates `CNOT` / `CZ`
      - repetitions `R1` / `R2`
      - trajectory-correlation metrics such as `Lam_MI_decay_fit`, `MI_traj_mean`, `dLam`, `dNegFrac`
  - there are no direct runner-name or key-string hits for either orphan in the current `simpy/` inventory
- bounded implication:
  - catalog adjacency alone is not enough to merge these two axis0 orphans; they belong to separate residual families

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:42-43,51-52`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the top-level catalog lists:
    - `axis0_boundary_bookkeep_v1`
    - `axis0_traj_corr_suite_v2`
  - the repo-held top-level evidence pack omits both filename aliases and both family names
- bounded implication:
  - the current orphan is catalog-visible by filename alias only and remains unadmitted in the evidence pack

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_boundary_bookkeep_sweep_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_traj_corr_suite_v2.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `BATCH_sims_leading_space_runner_result_family__v1/MANIFEST.json`
  - `BATCH_sims_axis0_traj_corr_suite_family__v1/MANIFEST.json`
  - `SIM_CATALOG_v1.3.md:42-43,51-52`
- bounded comparison read:
  - the earlier leading-space batch already anchored the wider boundary/bookkeep family via the sweep result surface
  - the current orphan is a compact result-only slice of that family
  - the neighboring `traj_corr_suite_v2` orphan stays separate and should be processed next as its own bounded unit

## 5) Source-Class Read
- Best classification:
  - residual result-only orphan slice of the already-anchored axis0 boundary/bookkeeping family
- Not best classified as:
  - a standalone fresh family with no prior anchor
  - part of the adjacent trajectory-correlation orphan
  - a top-level admitted sims family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - the stored surface fixes one sign, two sequences, and two init classes
    - bookkeeping deltas and reconstruction error summaries are explicit
    - negativity remains zero across all four stored payloads
  - theory-facing:
    - BELL carries much larger bookkeeping displacement than GINIBRE
    - the current slice is consistent with the REC1 part of the wider sweep family
  - evidence-facing:
    - the current orphan is source-linked to the already-batched sweep family through exact overlapping metrics
    - top-level visibility is catalog-only and absent from the evidence pack
- possible downstream consequence:
  - the next residual result-only pass should process `results_axis0_traj_corr_suite_v2.json` as a separate family rather than retroactively merging it into this boundary/bookkeep slice
