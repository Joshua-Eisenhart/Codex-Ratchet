# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_AB_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_mi_discrim_branches_ab.py` and `results_axis0_mi_discrim_branches_ab.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - explicit CNOT coupling is the decisive contract change that revives a real MI branch split
- supporting anchors:
  - runner AB-coupling step
  - nonzero MI means and nonzero MI delta

## Distillate D3
- strongest source-bound read:
  - AB coupling increases MI while reducing the absolute `SAgB` branch gap relative to the non-AB sibling
- supporting anchors:
  - current-vs-prior batch comparison metrics

## Distillate D4
- evidence assumptions extracted:
  - the catalog lists the AB family
  - the repo-held top-level evidence pack omits the current local SIM_ID
  - the current family is stronger as a stored runner/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - negative evidence-pack search

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `2` branches
    - `512` trials
    - `64` cycles
    - `1` axis3 sign
  - both stored branches keep `neg_SAgB_frac = 0.0`
  - the next residual paired family begins at `run_axis0_mutual_info.py`
- supporting anchors:
  - current runner contract
  - current result surface
  - residual ordering

## Distillate D6
- failure modes extracted:
  - mistaking the runner comment `the fix` for proof of repo-top admission
  - projecting the current MI signal backward onto the non-AB sibling
  - assuming nonzero MI here also implies negativity onset
- supporting anchors:
  - tension items `T1` through `T4`
