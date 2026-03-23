# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
Extraction mode: `SIM_ENGINE32_ATTACK_PASS`

## Distillate D1
- statement:
  - `engine32_axis0_axis6_attack` is a focused 32-cell attack lattice, not a composite precursor bundle
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:168-201`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- possible downstream consequence:
  - later engine-family work can reuse this as one coherent executable unit

## Distillate D2
- statement:
  - the family’s strongest stored signal is loop orientation:
    - outer `MIX_R` increases trajectory entropy and decreases purity
    - inner `MIX_R` decreases trajectory entropy and increases purity
- source anchors:
  - `results_engine32_axis0_axis6_attack.json:1-689`
- possible downstream consequence:
  - later summaries should foreground loop orientation before sequence detail

## Distillate D3
- statement:
  - the file’s “Axis0 attack” framing is narrowed by its own implementation to a one-qubit trajectory proxy with no AB coupling
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:111-121`
- possible downstream consequence:
  - later Axis0 comparisons should maintain this proxy boundary explicitly

## Distillate D4
- statement:
  - the stored JSON is richer than the script-local evidence block because it holds absolute stage metrics while the evidence block keeps only deltas
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:219-232`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- possible downstream consequence:
  - result-surface reading is required for full family reconstruction

## Distillate D5
- statement:
  - the family is catalog-present but not currently top-level evidence-pack-present in the repo
- source anchors:
  - `SIM_CATALOG_v1.3.md:54`
  - top-level evidence-pack search read in this batch
- possible downstream consequence:
  - provenance confidence should remain moderate and source-local

## Distillate D6
- statement:
  - the adjacent `full_axis_suite` is a separate cross-axis sampler family and should be processed next on its own
- source anchors:
  - `run_full_axis_suite.py:224-253`
  - `results_full_axis_suite.json:1-36`
- possible downstream consequence:
  - the next batch can preserve cross-axis sampler logic without diluting the engine32 attack lattice
