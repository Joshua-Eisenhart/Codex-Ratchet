# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_leading_space_runner_result_family__v1`
Extraction mode: `SIM_RUNNER_RESULT_PASS`

## Distillate D1
- statement:
  - the first executable-facing sims family in folder order is not one homogeneous experiment but three coupled runner/result pairs with different roles: compression sweep, linkage variant pack, and mega aggregate
- source anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:4-12`
  - ` run_axis12_axis0_link_v1.py:3-5`
  - ` run_mega_axis0_ab_stage16_axis6.py:3-5`
- possible downstream consequence:
  - later sims intake should preserve family identity rather than treating all early runners as one “starter suite”

## Distillate D2
- statement:
  - boundary bookkeeping is explicitly modeled as a reconstruction-bandwidth experiment over `REC1`, `REC3`, and `REC9`, and the result surface shows `REC9` behaving as a near-lossless class
- source anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:150-158`
  - `results_axis0_boundary_bookkeep_sweep_v2.json:21-167`
- possible downstream consequence:
  - later summary surfaces should distinguish lossy boundary compression from full-record sanity cases

## Distillate D3
- statement:
  - `run_axis12_axis0_link_v1.py` packages three named variants, but the current artifact couples those variants strongly to Axis12 bookkeeping and weakly or not at all to the stored Axis0 metrics
- source anchors:
  - ` run_axis12_axis0_link_v1.py:153-164`
  - ` run_axis12_axis0_link_v1.py:235-248`
  - `results_axis12_axis0_link_v1.json:2-720`
- possible downstream consequence:
  - this family is a strong candidate for later contradiction-preserving re-entry on “labelled linkage vs actual dependency”

## Distillate D4
- statement:
  - the mega family aggregates `16` Stage16 entries and `32` AB Axis0 entries across `4` seeds, making it the first visibly large mixed-family result surface in this sims lane
- source anchors:
  - ` run_mega_axis0_ab_stage16_axis6.py:249-370`
  - `results_mega_axis0_ab_stage16_axis6.json:2-350`
- possible downstream consequence:
  - later passes may need to split aggregate convenience from evidence interpretability

## Distillate D5
- statement:
  - directionality matters materially in the mega family: for `T1_BELL`, `SEQ04` is lower than `SEQ01` in forward MI by about `-0.0523`, but higher in reverse MI by about `+0.1396`
- source anchors:
  - `results_mega_axis0_ab_stage16_axis6.json:2-21`
  - `results_mega_axis0_ab_stage16_axis6.json:121-141`
- possible downstream consequence:
  - later summaries should preserve forward/reverse splits instead of collapsing sequence-order effects

## Distillate D6
- statement:
  - all three runners follow the same local engineering pattern: deterministic knob block, JSON write, code/output hashing, and sidecar `SIM_EVIDENCE` emission
- source anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:221-275`
  - ` run_axis12_axis0_link_v1.py:297-336`
  - ` run_mega_axis0_ab_stage16_axis6.py:249-378`
- possible downstream consequence:
  - later sidecar-evidence reconciliation can operate across this family without needing runtime execution in this lane
