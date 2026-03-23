# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_leading_space_runner_result_family__v1`
Extraction mode: `SIM_RUNNER_RESULT_PASS`

## Cluster S1: Boundary-record reconstruction sweep
- source anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:150-158`
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:160-215`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:21-167`
- cluster members:
  - `REC1`
  - `REC3`
  - `REC9`
  - `SEQ01`
  - `SEQ02`
  - sign `+/-`
  - `GINIBRE` / `BELL`
- compressed read:
  - this pair tests how much boundary-record compression changes reconstructed MI, `SAgB`, and Frobenius error under two sequence orders
- possible downstream consequence:
  - useful executable-facing family for record-bandwidth assumptions and reconstruction sensitivity

## Cluster S2: Axis12 linkage labeling
- source anchors:
  - ` run_axis12_axis0_link_v1.py:137-164`
  - ` run_axis12_axis0_link_v1.py:218-249`
  - `results_axis12_axis0_link_v1.json:173-240`
  - `results_axis12_axis0_link_v1.json:653-720`
- cluster members:
  - `canon`
  - `swap`
  - `rand`
  - `seta_bad`
  - `setb_bad`
  - `seni_within`
  - `nesi_within`
- compressed read:
  - the pair expresses Axis12 variation through combinatorial edge-class counts across four sequence orders and packages three named variant families
- possible downstream consequence:
  - useful for later separation of topology/constraint bookkeeping from dynamical metrics

## Cluster S3: Axis0 metric invariance across linkage variants
- source anchors:
  - ` run_axis12_axis0_link_v1.py:186-216`
  - ` run_axis12_axis0_link_v1.py:235-248`
  - `results_axis12_axis0_link_v1.json:3-172`
  - `results_axis12_axis0_link_v1.json:243-412`
  - `results_axis12_axis0_link_v1.json:483-652`
- cluster members:
  - `MI_mean`
  - `SAgB_mean`
  - `neg_SAgB_frac`
  - `plus` / `minus`
  - `ginibre` / `bell`
- compressed read:
  - despite the linkage framing, the Axis0 metric blocks are structurally duplicated across `canon`, `swap`, and `rand` because the axis0 path depends on sequence dynamics rather than the Axis12 variant sets
- possible downstream consequence:
  - later sims interpretation must not overstate cross-axis linkage based on the variant names alone

## Cluster S4: Stage16 plus AB aggregate packaging
- source anchors:
  - ` run_mega_axis0_ab_stage16_axis6.py:249-378`
  - `results_mega_axis0_ab_stage16_axis6.json:2-195`
  - `results_mega_axis0_ab_stage16_axis6.json:241-350`
- cluster members:
  - `stage16`
  - `axis0_ab`
  - `OUTER_AXIS6`
  - `INNER_AXIS6`
  - `FWD` / `REV`
  - `SEQ01`-`SEQ04`
  - `T1` / `T2`
- compressed read:
  - this pair bundles two families into one artifact: per-stage one-qubit uniform-vs-mix deltas and AB trajectory metrics relative to sequence order
- possible downstream consequence:
  - useful for aggregate pressure mapping, but later batches may need to split stage-level and AB-level claims

## Cluster S5: Evidence-pack emission contract
- source anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:256-275`
  - ` run_axis12_axis0_link_v1.py:251-340`
  - ` run_mega_axis0_ab_stage16_axis6.py:350-378`
- cluster members:
  - JSON write
  - code hash
  - output hash
  - named `SIM_ID`
  - `EVIDENCE_SIGNAL`
- compressed read:
  - all three runners follow the same local contract: serialize JSON, hash the code and payload, then emit one or more compact `SIM_EVIDENCE` blocks
- possible downstream consequence:
  - later source-bound checks can compare sidecar evidence packs against the generated top-level evidence-pack docs without executing the scripts

## Cluster S6: Filesystem hygiene hazard
- source anchors:
  - observed folder-order inventory in `sims/simpy`
- cluster members:
  - leading-space `.py` basenames
  - matching leading-space `.pyc` cache artifacts
  - paired result JSONs without the leading-space quirk
- compressed read:
  - this family’s defining filesystem feature is a path-hygiene irregularity at the runner level, not in the result filenames
- possible downstream consequence:
  - executable-facing tooling may need extra quoting/canonicalization discipline even when the result side is clean
