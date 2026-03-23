# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_channel_realization_suite_family__v1`
Extraction mode: `SIM_AXIS12_CHANNEL_REALIZATION_SUITE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis12_channel_realization_suite.py` and `results_axis12_channel_realization_suite.json` form one clean residual paired family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the family is a fixed-parameter axis12 edge-and-endpoint suite rather than a broad parameter scan
- supporting anchors:
  - one fixed `gamma/p/q/theta` tuple
  - four sequences
  - two sign realizations

## Distillate D3
- strongest source-bound read:
  - `SEQ02` is the strongest local endpoint channel realization under both signs
- supporting anchors:
  - lowest entropy and highest purity under sign `+1`
  - lowest entropy and highest purity under sign `-1`

## Distillate D4
- evidence assumptions extracted:
  - the local suite SIM_ID is omitted from the repo-held top-level evidence pack
  - the repo-held pack admits `S_SIM_AXIS12_CHANNEL_REALIZATION_V4` under the same runner hash
  - the current family is stronger as a local runner/result pair than as a repo-top admitted artifact
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - shared code hash `5e6358240110019fd266675f9ff1e520c7822114a811d597b630a62aa9efd6f5`

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `256` states
    - `64` cycles
    - four sequences
    - sign `+1` and sign `-1`
    - coarse `SENI/NESI` edge flags
    - endpoint entropy and purity summaries
  - the next residual paired family begins at `run_axis12_seq_constraints.py`
- supporting anchors:
  - current runner contract
  - residual ordering

## Distillate D6
- failure modes extracted:
  - mistaking the local suite for the repo-top `V4` descendant because the code hash matches
  - overreading the edge-flag partition as a complete endpoint-order explanation
  - forgetting that axis3 sign is globally directional inside this axis12 family
  - merging adjacent runner-only harden surfaces into the current paired batch
- supporting anchors:
  - tension items `T1` through `T5`
