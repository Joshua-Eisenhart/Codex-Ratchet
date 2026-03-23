# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_ultra4_full_stack_family__v1`
Extraction mode: `SIM_ULTRA4_FULL_STACK_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_ultra4_full_stack.py` and `results_ultra4_full_stack.json` form one bounded full-stack macro family
- supporting anchors:
  - raw-folder position
  - one runner plus one paired result surface

## Distillate D2
- strongest source-bound read:
  - ultra4 extends the ultra strip with a geometry-and-axis12 layer on top of the Stage16 and Axis0 AB branches
- supporting anchors:
  - `berry_flux_plus`
  - `berry_flux_minus`
  - `axis12`

## Distillate D3
- strongest source-bound read:
  - the `axis0_ab` branch is internally split between absolute `SEQ01` baselines and delta records for later sequences
- supporting anchors:
  - current runner contract
  - current result record shapes

## Distillate D4
- evidence assumptions extracted:
  - the catalog admits both `ultra4_full_stack` and `ultra_axis0_ab_axis6_sweep`
  - the repo-held top-level evidence pack admits neither family
  - the full-stack surface is stronger as a stored executable/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:117,131,148-149`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - ultra4 uses `2048` Stage16 states, `128` Axis0 trials, `64` Axis0 cycles, and `4` stored sequences
  - the Berry-flux layer is sign-symmetric
  - the largest Axis0 AB deltas concentrate in `SEQ04` reverse Bell settings
- supporting anchors:
  - current runner contract
  - current result extrema

## Distillate D6
- failure modes extracted:
  - flattening the full-stack shell into one single effect scale
  - treating the `axis0_ab` map as if every record had the same contract
  - merging the adjacent ultra sweep into this batch because of macro similarity and raw-order adjacency
- supporting anchors:
  - tension items `T2` through `T6`
