# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_negsagb_stress_family__v1`
Extraction mode: `SIM_AXIS0_NEGSAGB_STRESS_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_negsagb_stress.py` and `results_axis0_negsagb_stress.json` form one clean residual paired search family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the stored search fully exhausts its `3456`-record parameter grid and still finds no positive negativity score
- supporting anchors:
  - `records_count = 3456`
  - `best.score = 0.0`

## Distillate D3
- strongest source-bound read:
  - the stored result surface is highly compressed relative to the executed search
- supporting anchors:
  - `best`
  - `records_sample[:10]`
  - full-grid runner definition

## Distillate D4
- evidence assumptions extracted:
  - the catalog lists the family
  - the repo-held top-level evidence pack omits the local SIM_ID
  - the current family is stronger as a stored runner/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - negative evidence-pack search

## Distillate D5
- runtime expectations extracted:
  - one run covers:
    - `2` branch orders
    - `2` axis3 signs
    - `4` cycle values
    - `36` noise tuples
    - `2` entanglers
    - `3` entangle repetition counts
    - `2` entangle positions
  - the next residual paired family begins at `run_axis0_sagb_entangle_seed.py`
- supporting anchors:
  - runner sweep definition
  - residual ordering

## Distillate D6
- failure modes extracted:
  - mistaking search breadth for search success
  - treating the stored `best` record as if it retained the whole sweep
  - assuming the larger stress family supersedes the smaller mutual-info baseline on stored negativity
- supporting anchors:
  - tension items `T1` through `T4`
