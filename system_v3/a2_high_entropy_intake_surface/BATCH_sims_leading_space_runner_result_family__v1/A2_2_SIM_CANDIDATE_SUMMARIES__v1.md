# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_leading_space_runner_result_family__v1`
Extraction mode: `SIM_RUNNER_RESULT_PASS`

## Candidate Summary C1
- proposal-only reading:
  - the first runner/result sims family is already good enough to separate three executable-facing concerns:
    - record-bandwidth reconstruction
    - Axis12 bookkeeping variants
    - larger Stage16 plus AB aggregation
- supporting anchors:
  - selected runner/result pairs across the batch

## Candidate Summary C2
- proposal-only reading:
  - one reusable family pattern here is `runner advertises output contract -> result JSON exposes the real shape -> sidecar evidence is deferred`
- supporting anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:9-12`
  - ` run_axis12_axis0_link_v1.py:3-5`
  - ` run_mega_axis0_ab_stage16_axis6.py:3-5`

## Candidate Summary C3
- proposal-only reading:
  - the strongest executable-facing contradiction in this batch is that the Axis12 linkage runner names a cross-axis link while the stored Axis0 payload is invariant across `canon`, `swap`, and `rand`
- supporting anchors:
  - ` run_axis12_axis0_link_v1.py:153-164`
  - ` run_axis12_axis0_link_v1.py:235-248`
  - `results_axis12_axis0_link_v1.json:2-720`

## Candidate Summary C4
- proposal-only reading:
  - the strongest runtime expectation family is deterministic knob-driven generation with explicit seeds/trials/cycles and hashable serialized outputs
- supporting anchors:
  - ` run_axis0_boundary_bookkeep_sweep_v2.py:221-275`
  - ` run_axis12_axis0_link_v1.py:297-336`
  - ` run_mega_axis0_ab_stage16_axis6.py:249-378`

## Candidate Summary C5
- proposal-only quarantine:
  - do not flatten the following together without later re-entry:
    - lossy record sweeps and near-lossless `REC9`
    - Axis12 bookkeeping counts and Axis0 dynamical metrics
    - one-qubit Stage16 deltas and AB trajectory suites
    - clean result filenames and irregular runner filenames
- supporting anchors:
  - all six selected sources

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch in folder order should begin at `axis4_seq_cycle_sim.py` and its nearest result/evidence siblings, with explicit attention to whether that family sharpens the Axis4 variance-order seam already exposed in the top-level docs
- supporting anchors:
  - deferred next meaningful noncache source in current batch selection
