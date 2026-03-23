# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1`
Extraction mode: `SIM_ULTRA_AXIS0_AB_AXIS6_SWEEP_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_ultra_axis0_ab_axis6_sweep.py` and `results_ultra_axis0_ab_axis6_sweep.json` form one bounded final ultra sweep family
- supporting anchors:
  - raw-folder position
  - one runner plus one paired result surface

## Distillate D2
- strongest source-bound read:
  - the current family is a narrowed ultra shell that keeps Stage16 and Axis0 AB sweep structure while dropping geometry and Axis12
- supporting anchors:
  - current runner contract
  - comparison to `ultra4`

## Distillate D3
- strongest source-bound read:
  - the `axis0_ab` branch is internally split between absolute `SEQ01` baselines and delta records for later sequences
- supporting anchors:
  - current runner contract
  - current result record shapes

## Distillate D4
- evidence assumptions extracted:
  - the catalog admits both `ultra4_full_stack` and the current ultra sweep family
  - the repo-held top-level evidence pack admits neither family
  - the current family is stronger as a stored executable/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:117,131,148-149`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - the current runner uses `8` seeds, `2048` Stage16 states, `256` Axis0 trials, `64` Axis0 cycles, `4` sequences, `2` entanglers, and `4` mix modes
  - the strongest Axis0 AB deltas concentrate in `SEQ04` reverse Bell settings
  - the strongest Stage16 cells remain Se-focused
- supporting anchors:
  - current runner contract
  - current result extrema

## Distillate D6
- failure modes extracted:
  - flattening the final ultra sweep shell into one single effect scale
  - treating the `axis0_ab` map as if every record had the same contract
  - missing that the raw-order `simpy/` strip ends at this file
- supporting anchors:
  - tension items `T2` through `T6`
