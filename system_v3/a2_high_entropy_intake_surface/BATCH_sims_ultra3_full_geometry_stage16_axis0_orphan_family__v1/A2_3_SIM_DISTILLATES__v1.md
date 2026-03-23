# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
Extraction mode: `SIM_ULTRA3_FULL_GEOMETRY_STAGE16_AXIS0_ORPHAN_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly reopens `results_ultra3_full_geometry_stage16_axis0.json` as its own bounded result-only ultra family
- supporting anchors:
  - prior axis0 traj-corr v2 orphan manifest
  - current source membership

## Distillate D2
- strongest source-bound read:
  - the current orphan is a geometry-bearing ultra surface with `128` `axis0_ab` entries, `48` `stage16` entries, and `4` stored sequences
- supporting anchors:
  - current structural counts
  - current top-level key map

## Distillate D3
- strongest source-bound read:
  - the strongest stored `axis0_ab` perturbation sits on `T1_REV_BELL_CNOT_R1_SEQ04`, while the strongest `stage16` cell sits on `T1_outer_1_Se_UP_MIX_A`
- supporting anchors:
  - current `axis0_ab` extrema
  - current `stage16` extrema

## Distillate D4
- strongest source-bound read:
  - the current orphan belongs near the earlier ultra strip, but it is a middle seam rather than the same family as ultra4 or the final ultra sweep
- supporting anchors:
  - current ultra-strip comparisons

## Distillate D5
- evidence assumptions extracted:
  - the current orphan is catalog-visible by filename alias only
  - the repo-held evidence pack omits it entirely
  - no runner is admitted as a source member in this bounded batch
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - current source membership

## Distillate D6
- failure modes extracted:
  - merging `ultra3` into ultra4 because both have berry flux
  - merging `ultra3` into the final ultra sweep because both have `stage16` and `axis0_ab`
  - merging `ultra3` into `ultra_big` because of catalog adjacency
  - treating the `axis0_ab` map as one uniform record contract
  - overstating the berry-flux layer as exact `±2pi`
- supporting anchors:
  - tension items `T1` through `T6`
