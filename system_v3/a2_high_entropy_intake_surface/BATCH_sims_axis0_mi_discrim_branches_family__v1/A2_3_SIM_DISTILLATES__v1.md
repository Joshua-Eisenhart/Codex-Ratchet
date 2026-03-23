# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_mi_discrim_branches_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_mi_discrim_branches.py` and `results_axis0_mi_discrim_branches.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the stored non-AB branch family discriminates `SAgB`, not MI
- supporting anchors:
  - machine-scale MI means and MI delta
  - nonzero `delta_SAgB_mean_SEQ02_minus_SEQ01`

## Distillate D3
- strongest source-bound read:
  - the adjacent `_ab` sibling is the meaningful comparison boundary because it adds explicit AB coupling and revives a real MI signal
- supporting anchors:
  - `apply_unitary_AB(rho, CNOT)` in the sibling
  - nonzero sibling MI means and MI delta

## Distillate D4
- evidence assumptions extracted:
  - the catalog lists both the current non-AB family and the `_ab` sibling
  - the repo-held top-level evidence pack omits the current local SIM_ID
  - the current family is stronger as a stored runner/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - negative evidence-pack search

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `2` branch orders
    - `512` trials
    - `64` cycles
    - `1` axis3 sign
  - both stored branches keep `neg_SAgB_frac = 0.0`
- supporting anchors:
  - current runner contract
  - current result surface

## Distillate D6
- failure modes extracted:
  - treating the family name as proof of a real MI discriminator
  - collapsing the non-AB family into the adjacent `_ab` family
  - mistaking local evidence emission for repo-top evidence-pack admission
- supporting anchors:
  - tension items `T1` through `T5`
