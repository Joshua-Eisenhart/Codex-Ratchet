# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1`
Extraction mode: `SIM_AXIS0_HISTORYOP_REC_SUITE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_historyop_rec_suite_v1.py` and `results_axis0_historyop_rec_suite_v1.json` form one clean residual paired family
- supporting anchors:
  - residual closure audit
  - one runner plus one paired result

## Distillate D2
- strongest source-bound read:
  - the family is internally a four-case reconstruction sweep over one shared axis0 history-operator experiment
- supporting anchors:
  - four local SIM_IDs
  - shared trials, cycles, sequences, and run keys

## Distillate D3
- strongest source-bound read:
  - reconstruction mode changes stored error magnitude but leaves stored trajectory MI means unchanged
- supporting anchors:
  - rec-mode average `ERR_traj` means
  - rec-mode average `MI_traj` means

## Distillate D4
- evidence assumptions extracted:
  - the catalog lists this family
  - the repo-held top-level evidence pack omits all four local SIM_IDs
  - the runner still defines a local evidence contract for each case
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - negative evidence-pack search
  - runner evidence-emission block

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `4` rec modes
    - `2` init modes
    - `2` axis3 signs
    - `4` sequences
    - `256` trials
    - `16` cycles
  - `NEG_SAgB_end_frac` stays at `0.0` throughout the stored family
- supporting anchors:
  - runner suite definition
  - stored result cases

## Distillate D6
- failure modes extracted:
  - treating local evidence emission as repo-top admission
  - assuming larger reconstruction error changes trajectory MI in this family
  - assuming the compact `SEQ02-SEQ01` summary captures every important stored effect
- supporting anchors:
  - tension items `T1` through `T5`
