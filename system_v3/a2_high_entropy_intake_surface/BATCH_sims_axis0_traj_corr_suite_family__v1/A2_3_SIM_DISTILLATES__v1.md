# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_traj_corr_suite_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_traj_corr_suite.py` and `results_axis0_traj_corr_suite.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the family is a 32-case suite over sign, init mode, direction, and sequence rather than a compact branch pair
- supporting anchors:
  - four sequences
  - two directions
  - two signs
  - two init modes

## Distillate D3
- strongest source-bound read:
  - Bell keeps stored trajectory negativity across the suite while Ginibre stays at zero negativity across the suite
- supporting anchors:
  - nonzero Bell `SAgB_neg_frac_traj`
  - zero Ginibre `SAgB_neg_frac_traj`

## Distillate D4
- evidence assumptions extracted:
  - the local suite SIM_ID is not repo-top admitted
  - the repo-held top-level evidence pack admits `V4` and `V5` descendants under the same runner hash
  - the emitted evidence block is a compressed delta view rather than the full result surface
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json`

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `128` trials
    - `64` cycles
    - `4` sequences
    - `2` directions
    - `2` signs
    - `2` init modes
    - `1` CNOT repetition per terrain step
  - the next residual paired family begins at `run_axis12_channel_realization_suite.py`
- supporting anchors:
  - current runner contract
  - residual ordering

## Distillate D6
- failure modes extracted:
  - collapsing the local suite into `V4` or `V5` just because the code hash matches
  - mistaking the delta-only evidence block for the full 32-case surface
  - treating `SEQ04` as direction-invariant
  - overstating exact sign symmetry
- supporting anchors:
  - tension items `T1` through `T5`
