# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_topology4_channelgrid_family__v1`
Extraction mode: `SIM_AXIS12_TOPOLOGY4_CHANNELGRID_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis12_topology4_channelgrid_v1.py` and `results_axis12_topology4_channelgrid_v1.json` form the final clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - paired-family completion check

## Distillate D2
- strongest source-bound read:
  - the family is defined by a clean topology4 quadrant contract plus an explicit test-vs-control sign layer
- supporting anchors:
  - four topology4 quadrants
  - `n_test` vs `n_ctrl`

## Distillate D3
- strongest source-bound read:
  - adaptive families carry the nonlinearity signal while fixed families are effectively linear
- supporting anchors:
  - `AD` vs `FX` `lin_err_mean` values

## Distillate D4
- evidence assumptions extracted:
  - the current local channelgrid SIM_ID is not repo-top admitted
  - the neighboring terrain8 topology4 surface remains the admitted artifact in the same strip
  - clean local pairing is not the same thing as evidence-pack admission
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - neighboring terrain8 seam batch

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `4` topology4 families
    - `4096` sampled states
    - `512` linearity trials
    - explicit test and control axes
  - residual paired-family intake is complete after this batch
- supporting anchors:
  - current runner contract
  - paired-family completion check

## Distillate D6
- failure modes extracted:
  - mistaking control-axis success for total absence of test-axis sign effects
  - collapsing topology4 behavior into one scalar strength ranking
  - merging this clean local pair into the prior terrain8 seam batch
  - assuming paired-family completion means all residual classes are done
- supporting anchors:
  - tension items `T1` through `T6`
