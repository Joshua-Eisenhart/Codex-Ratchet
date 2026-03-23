# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis0_mutual_info_family__v1`
Extraction mode: `SIM_AXIS0_MUTUAL_INFO_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_axis0_mutual_info.py` and `results_axis0_mutual_info.json` form one clean residual paired baseline family
- supporting anchors:
  - one runner plus one paired result
  - prior residual pair ordering

## Distillate D2
- strongest source-bound read:
  - the current stored output does produce negative conditional entropy, but only at a one-in-512 scale
- supporting anchors:
  - `neg_SAgB_frac = 0.001953125`
  - `SAgB_min = -0.002114071978150056`

## Distillate D3
- strongest source-bound read:
  - the runner’s local kill path exists, but the stored output does not trigger it
- supporting anchors:
  - conditional `KILL_SIGNAL` emission in the runner
  - current nonzero negativity fraction

## Distillate D4
- evidence assumptions extracted:
  - the catalog lists the family
  - the repo-held top-level evidence pack omits the local SIM_ID and kill token
  - the current family is stronger as a stored runner/result pair than as a repo-top evidenced artifact
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - negative evidence-pack search

## Distillate D5
- runtime expectations extracted:
  - one run covers `512` Ginibre two-qubit states with no branch decomposition
  - the adjacent `negsagb_stress` family is the next residual search-style pair
  - the larger stress sweep currently stores no negativity despite its broader search surface
- supporting anchors:
  - current runner contract
  - current result surface
  - stress comparison

## Distillate D6
- failure modes extracted:
  - treating positive MI as if it proved robust negativity
  - treating the current tiny negativity fraction as stronger than it is
  - mistaking local evidence emission for repo-top evidence-pack admission
- supporting anchors:
  - tension items `T1` through `T4`
