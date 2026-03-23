# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_topology4_channelfamily_terrain8_seam__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELFAMILY_TERRAIN8_SEAM_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch is correctly centered on a provenance seam, not a normal clean runner/result pair
- supporting anchors:
  - same runner hash on both selected sources
  - incompatible current output contract and admitted surface contract

## Distillate D2
- strongest source-bound read:
  - the current executable-facing runner implements a topology4 channel-family suite with four family keys and five metrics per family
- supporting anchors:
  - `EO_FX`, `EO_AD`, `EC_FX`, `EC_AD`
  - local result `results_axis12_topology4_channelfamily_suite_v2.json`

## Distillate D3
- strongest source-bound read:
  - the admitted terrain8 surface carries terrain-specific sign structure, with `Si` strongest overall and nonuniform sign effects across terrains
- supporting anchors:
  - lowest entropy / highest purity on `Si_sign-1`
  - `Se` improves under sign `+1`
  - `Si` worsens under sign `+1`

## Distillate D4
- evidence assumptions extracted:
  - repo-top evidence directly admits the selected terrain8 surface
  - the current local runner SIM_ID is not repo-top admitted
  - exact output admission can coexist with naming and contract drift
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - selected output hash `218b43b4a1adee0149363f5103840329693d81e82beea73485fdc1235e2a6e9a`

## Distillate D5
- runtime expectations extracted:
  - the current runner would write:
    - `results_axis12_topology4_channelfamily_suite_v2.json`
    - one local `CHANNELFAMILY_SUITE_V2` evidence block
  - the next residual paired family begins at `run_axis12_topology4_channelgrid_v1.py`
- supporting anchors:
  - current runner contract
  - residual ordering

## Distillate D6
- failure modes extracted:
  - smoothing the admitted terrain8 surface into the current local topology4-family contract because the hash matches
  - ignoring the runner's own local result file and losing the seam entirely
  - assuming terrain sign effects are uniform because the admitted surface has only one fixed parameter tuple
  - collapsing the next topology4 channelgrid pair into the current batch
- supporting anchors:
  - tension items `T1` through `T6`
