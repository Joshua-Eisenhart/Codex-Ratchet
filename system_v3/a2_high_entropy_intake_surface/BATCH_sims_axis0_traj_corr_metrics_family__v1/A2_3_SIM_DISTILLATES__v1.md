# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_traj_corr_metrics_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_METRICS_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_traj_corr_metrics.py` and `results_axis0_traj_corr_metrics.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the family is defined by dual-init trajectory tracking rather than one fixed state-preparation regime
- supporting anchors:
  - one run covers `GINIBRE` and `BELL`
  - the runner stores trajectory means, fitted lambdas, and trajectory negativity fractions

## Distillate D3
- strongest source-bound read:
  - Bell initialization preserves nonzero stored trajectory negativity while Ginibre initialization stays strictly nonnegative over the stored trajectory
- supporting anchors:
  - Bell `SAgB_neg_frac_traj` near `0.097`
  - Ginibre `SAgB_neg_frac_traj = 0.0`

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
    - `256` trials
    - `64` cycles
    - `1` CNOT repetition per terrain step
    - shared sequence pair `SEQ01` / `SEQ02`
    - both `GINIBRE` and `BELL` init modes
  - the next residual paired family begins at `run_axis0_traj_corr_suite.py`
- supporting anchors:
  - current runner contract
  - residual ordering

## Distillate D6
- failure modes extracted:
  - mistaking trajectory negativity for negative final-state conditional entropy
  - mistaking small sequence-order deltas for init-independent directionality
  - mistaking local evidence emission for repo-top evidence-pack admission
- supporting anchors:
  - tension items `T1` through `T5`
