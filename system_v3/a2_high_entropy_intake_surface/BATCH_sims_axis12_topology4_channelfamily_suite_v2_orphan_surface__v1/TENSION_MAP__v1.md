# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis12_topology4_channelfamily_suite_v2_orphan_surface__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_SUITE_V2_ORPHAN_SURFACE_PASS`

## T1) The local channelfamily result was already read in the earlier seam batch, but only as comparison-only
- source markers:
  - prior seam manifest
  - current local result surface
- tension:
  - the file was known and intentionally excluded from source membership earlier
  - the direct-source coverage audit later showed that exclusion left one uncovered sims file
- preserved read:
  - keep both facts: the original seam decision was deliberate, and the coverage gap was real
- possible downstream consequence:
  - closure reporting must preserve the correction history rather than smoothing it away

## T2) The earlier terrain8-admission seam remains valid even after local source admission
- source markers:
  - prior seam manifest
- tension:
  - the seam batch preserved a mismatch between:
    - local channelfamily output contract
    - repo-top admitted terrain8 surface under the same runner hash
  - this correction batch source-admits the local result without replacing the seam logic
- preserved read:
  - current source admission does not cancel the earlier mismatch-preservation read
- possible downstream consequence:
  - later synthesis should cite both batches together when discussing this runner family

## T3) The local surface is compact and meaningful, but it was not enough to force source admission during the original seam pass
- source markers:
  - current local result surface
- tension:
  - the file clearly contains structured topology4 family metrics
  - the earlier batch still chose to foreground the admission seam instead
- preserved read:
  - preserve the earlier prioritization choice rather than rewriting history as oversight only
- possible downstream consequence:
  - future closure passes should distinguish “intentionally comparison-only” from “never examined”

## T4) Adaptive-vs-fixed and EC-vs-EO splits remain visible even in this minimal orphan surface
- source markers:
  - current local result surface
- tension:
  - adaptive families carry nontrivial `lin_err_mean`
  - fixed families are effectively linear
  - `EO_FX` carries the largest `deltaH_absmean`
- preserved read:
  - the local surface retains substantive structure despite its small size
- possible downstream consequence:
  - compact orphan surfaces should still be evaluated on content, not only on file size

## T5) The earlier “full closure” claim was premature by one file
- source markers:
  - hygiene manifest
  - aggregate coverage scan
- tension:
  - the prior hygiene batch correctly exhausted known residual artifact classes
  - the aggregate scan still found one uncovered sims file afterward
- preserved read:
  - closure completion happened only after this correction batch
- possible downstream consequence:
  - final closure summaries should mark this batch as the true 120-of-120 completion point

## T6) After this batch, the sims-side intake is complete in both residual-class and direct-source coverage terms
- source markers:
  - aggregate coverage rerun after this batch
- tension:
  - earlier residual-class completion and direct-source coverage completion did not coincide
  - they do coincide only now
- preserved read:
  - keep the two closure notions separate until this exact batch reunifies them
- possible downstream consequence:
  - no further sims-side intake batches are needed after this correction
