# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1`
Extraction mode: `SIM_ULTRA2_MACRO_BUNDLE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_ultra2_axis0_ab_stage16_axis6.py` and `results_ultra2_axis0_ab_stage16_axis6.json` form one bounded macro composite family
- supporting anchors:
  - raw-folder position
  - one runner plus one paired result surface

## Distillate D2
- strongest source-bound read:
  - the ultra2 family bundles three distinct subfamilies into one result:
    - `stage16`
    - `axis0_ab`
    - `axis12`
- supporting anchors:
  - current runner contract
  - current result keys

## Distillate D3
- strongest source-bound read:
  - the stored `seqs` field understates sequence participation for the Axis12 branch
- supporting anchors:
  - `seqs` lists only `SEQ01` / `SEQ02`
  - `axis12` also stores `SEQ03` / `SEQ04` counts

## Distillate D4
- evidence assumptions extracted:
  - the catalog admits both `ultra2` and `ultra4`
  - the repo-held top-level evidence pack admits neither macro SIM_ID
  - current macro surfaces are stronger as stored executable/result pairs than as repo-top evidenced artifacts
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:115,131,147-148`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - ultra2 uses `4` seeds, `4096` Stage16 states, `256` Axis0 trials, and `64` Axis0 cycles
  - the Stage16 branch is Se-concentrated and small-scale
  - the Axis0 AB branch is smaller-scale still
  - the Axis12 branch contributes discrete adjacency counts
- supporting anchors:
  - current runner contract
  - current result extrema

## Distillate D6
- failure modes extracted:
  - treating the bundled `seqs` field as if it fully declared Axis12 sequence scope
  - flattening Stage16, Axis0 AB, and Axis12 into one uniform behavior class
  - merging `ultra4` into the same batch because of macro similarity and raw-order adjacency
- supporting anchors:
  - tension items `T2` through `T6`
