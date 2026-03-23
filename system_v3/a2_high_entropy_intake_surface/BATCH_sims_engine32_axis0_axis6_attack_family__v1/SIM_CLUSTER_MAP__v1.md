# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
Extraction mode: `SIM_ENGINE32_ATTACK_PASS`

## Cluster S1: 32-cell attack lattice
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:168-201`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- cluster members:
  - `T1`
  - `T2`
  - `SEQ01`
  - `SEQ02`
  - `SEQ03`
  - `SEQ04`
  - `outer`
  - `inner`
  - `UNIFORM`
  - `MIX_R`
- compressed read:
  - the family is one explicit 2 x 4 x 2 x 2 lattice, not a loose bundle of nearby runs
- possible downstream consequence:
  - later summaries can treat this as one stable executable attack grid

## Cluster S2: Axis0 proxy simplification
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:111-121`
- cluster members:
  - `Axis0 proxy score`
  - `trajectory entropy mean`
  - `trajectory purity mean`
  - `No AB coupling in this batch`
- compressed read:
  - despite the Axis0 attack name, the script explicitly narrows the family to one-qubit trajectory readouts
- possible downstream consequence:
  - later Axis0 comparisons should not silently group this with AB-correlation families

## Cluster S3: Outer vs inner sign-stable delta pattern
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:219-227`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- cluster members:
  - outer-loop deltas
  - inner-loop deltas
  - entropy
  - purity
- compressed read:
  - across all stored types and sequences:
    - outer `MIX_R - UNIFORM` entropy deltas are positive
    - outer purity deltas are negative
    - inner entropy deltas are negative
    - inner purity deltas are positive
- possible downstream consequence:
  - this family has a strong loop-orientation signature that is more stable than its sequence modulation

## Cluster S4: Stage-local evidence compression
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:219-232`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- cluster members:
  - absolute cell metrics in JSON
  - delta-only evidence lines
  - one SIM_ID
- compressed read:
  - the result surface stores absolute stage metrics for all 32 cells, but the evidence packet compresses that to delta-only summaries against the uniform baseline
- possible downstream consequence:
  - later evidence consumers can miss absolute-state structure if they rely only on the evidence block

## Cluster S5: Missing top-level evidence-pack admission
- source anchors:
  - `SIM_CATALOG_v1.3.md:54`
  - top-level evidence-pack search read in this batch
- cluster members:
  - cataloged result stub `engine32_axis0_axis6_attack`
  - absent top-level `S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK` block
- compressed read:
  - the family is catalog-visible but not presently surfaced in the repo-held top-level evidence pack
- possible downstream consequence:
  - this batch should stay proposal-side and source-local about provenance strength

## Cluster S6: Adjacent cross-axis sampler exclusion
- source anchors:
  - `run_full_axis_suite.py:224-253`
  - `results_full_axis_suite.json:1-36`
- cluster members:
  - six-block cross-axis sampler
  - standalone descendants for axes 3/4/5/6
- compressed read:
  - the next raw-order file is structurally a different source class inside `sims`: a sampler/precursor family, not the same attack lattice
- possible downstream consequence:
  - the next batch should start from `full_axis_suite` as its own family
