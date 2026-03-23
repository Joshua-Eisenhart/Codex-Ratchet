# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_V2_ORPHAN_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly reopens `results_axis0_traj_corr_suite_v2.json` as its own bounded result-only family
- supporting anchors:
  - prior boundary/bookkeep orphan manifest
  - current source membership

## Distillate D2
- strongest source-bound read:
  - the current orphan uses a seq01-baseline-plus-deltas contract over a 32-prefix hidden lattice
- supporting anchors:
  - current base and delta counts
  - current `T1` / `T2` prefix counts

## Distillate D3
- strongest source-bound read:
  - the strongest stored perturbation concentrates on `T1_REV_BELL_CNOT_R1_SEQ04`
- supporting anchors:
  - current max absolute delta metrics

## Distillate D4
- strongest source-bound read:
  - the current orphan is related to the earlier local trajectory-correlation family, but it changes both storage and lattice structure and cannot be merged with that family
- supporting anchors:
  - current local-family comparison

## Distillate D5
- evidence assumptions extracted:
  - the current orphan is catalog-visible by filename alias only
  - the evidence pack omits it entirely
  - no direct runner-name hit is recoverable in current `simpy/`
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - current `simpy/` inventory check

## Distillate D6
- failure modes extracted:
  - inventing a runner anchor that is not present
  - treating missing absolute `SEQ02-04` entries as absent runs instead of delta encoding
  - collapsing the orphan into the earlier local suite or into repo-top `V4` / `V5`
  - ignoring the hidden `T1` / `T2` axis
  - mistaking catalog presence for evidence admission
- supporting anchors:
  - tension items `T1` through `T6`
