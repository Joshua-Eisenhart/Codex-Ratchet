# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_leading_space_runner_result_family__v1`
Extraction mode: `SIM_RUNNER_RESULT_PASS`

## T1) Repeatable-run contract vs leading-space runner paths
- source markers:
  - leading-space basenames in selected `simpy` paths
  - shared engineering expectations carried from the prior top-level sims batch
- tension:
  - these runners present themselves as ordinary executable harnesses
  - their literal leading-space basenames create shell/path-handling friction not present on the result side
- preserved read:
  - keep this as executable-facing hygiene risk rather than proof of invalid science or invalid results
- possible downstream consequence:
  - later executable-facing audit should keep path quoting/canonicalization visible

## T2) Boundary-bookkeeping sweep mixes near-lossless and lossy record classes
- source markers:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:150-158`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:47-52`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:154-160`
- tension:
  - `REC1` and `REC3` behave as compressed record classes with visible reconstruction error
  - `REC9` behaves as a near-lossless/full-record class with essentially zero delta and Frobenius error
- preserved read:
  - do not smooth `REC9` into the same evidence class as the narrower record sets
- possible downstream consequence:
  - later sims interpretation should distinguish compression stress from full-record sanity cases

## T3) Axis12/Axis0 linkage label vs actual dependency path
- source markers:
  - ` run_axis12_axis0_link_v1.py:153-164`
  - ` run_axis12_axis0_link_v1.py:186-216`
  - ` run_axis12_axis0_link_v1.py:235-248`
  - `results_axis12_axis0_link_v1.json:2-720`
- tension:
  - the runner is named as an Axis12/Axis0 linkage experiment
  - in the actual code and result layout, Axis12 variant sets change the combinatorial `axis12` counts while the `axis0` metrics are identical across `canon`, `swap`, and `rand`
- preserved read:
  - keep the linkage claim provisional and source-local; the current artifact shows label coupling stronger than metric coupling
- possible downstream consequence:
  - later batches should avoid over-reading cross-axis causation from this family alone

## T4) Mega aggregate bundles two evidence families into one file
- source markers:
  - ` run_mega_axis0_ab_stage16_axis6.py:276-290`
  - `results_mega_axis0_ab_stage16_axis6.json:2-195`
  - `results_mega_axis0_ab_stage16_axis6.json:241-350`
- tension:
  - the file combines one-qubit Stage16 deltas and AB Axis0 trajectory suites in one result surface
  - this helps packaging but blurs family boundaries for later interpretation
- preserved read:
  - keep Stage16 and AB Axis0 as adjacent but distinct subfamilies inside the aggregate
- possible downstream consequence:
  - future re-entry may need separate Stage16 and AB-specific batches

## T5) Sequence-order effects are not uniform across direction and family
- source markers:
  - `results_mega_axis0_ab_stage16_axis6.json:21`
  - `results_mega_axis0_ab_stage16_axis6.json:141`
- tension:
  - in the mega aggregate, `SEQ04` vs `SEQ01` can depress `MI_traj_mean` in one direction (`T1_BELL_FWD`) while elevating it strongly in another (`T1_BELL_REV`)
- preserved read:
  - keep direction-specific sequence behavior visible instead of flattening it into one generic `SEQ04 is better/worse` claim
- possible downstream consequence:
  - later executable/result passes should preserve directionality whenever summarizing sequence effects

## T6) Sidecar evidence-pack contract vs current batch boundary
- source markers:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:10-11`
  - ` run_axis12_axis0_link_v1.py:4-5`
  - ` run_mega_axis0_ab_stage16_axis6.py:4-5`
- tension:
  - each runner claims to produce an evidence-pack sidecar in addition to the JSON result
  - this bounded batch intentionally processes only the runners and their paired JSON outputs, not those sidecars
- preserved read:
  - this is a runner/result mapping batch, not a sidecar evidence reconciliation batch
- possible downstream consequence:
  - later intake can compare these runners to the generated evidence-pack surfaces without reopening this batch’s scope
