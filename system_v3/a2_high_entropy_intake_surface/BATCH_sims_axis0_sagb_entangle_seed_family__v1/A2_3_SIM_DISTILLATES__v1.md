# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_sagb_entangle_seed_family__v1`
Extraction mode: `SIM_AXIS0_SAGB_ENTANGLE_SEED_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_sagb_entangle_seed.py` and `results_axis0_sagb_entangle_seed.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the family stores effectively deterministic branch metrics despite randomized Bell-seed scrambling
- supporting anchors:
  - branch MI and `SAgB` ranges at floating-point-noise scale

## Distillate D3
- strongest source-bound read:
  - weak noise plus repeated CNOT coupling still does not produce any stored negative `S(A|B)` event
- supporting anchors:
  - both branch `neg_SAgB_frac` values equal `0.0`
  - positive `SAgB_min` in both branches

## Distillate D4
- evidence assumptions extracted:
  - the catalog lists the family
  - the repo-held top-level evidence pack omits the local SIM_ID
  - the current family is stronger as a stored runner/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - negative evidence-pack search

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - Bell-state seeds
    - `512` trials
    - `64` cycles
    - weak noise on `A`
    - `2` CNOT repetitions per terrain step
  - the next residual paired family begins at `run_axis0_traj_corr_metrics.py`
- supporting anchors:
  - current runner contract
  - residual ordering

## Distillate D6
- failure modes extracted:
  - projecting negativity onto the family because the setup looks strongly entangling
  - mistaking randomized Bell scrambles for meaningful trial-level output variance
  - mistaking local evidence emission for repo-top evidence-pack admission
- supporting anchors:
  - tension items `T1` through `T5`
