# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
Extraction mode: `SIM_AXIS0_BOUNDARY_BOOKKEEP_V1_ORPHAN_SLICE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because it is the next remaining result-only orphan and it has an exact family anchor through the already-batched boundary-bookkeep sweep
- supporting anchors:
  - current source membership
  - sweep-family overlap

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at one source member, because `results_axis0_traj_corr_suite_v2.json` is structurally separate and should not be merged on catalog adjacency alone
- supporting anchors:
  - current source membership
  - current separation read

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “compact enriched sign1/REC1 bookkeeping slice with strong BELL-vs-GINIBRE separation and zero negativity”
- supporting anchors:
  - current payload metrics

## Candidate Summary C4
- proposal-only quarantine:
  - do not describe this orphan as source-unanchored, because its overlapping mean metrics match the already-batched sweep family exactly
- supporting anchors:
  - current sweep-family comparison

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge `traj_corr_suite_v2` into this batch, because its 128-case trajectory lattice and metric contract are from a different family class
- supporting anchors:
  - current trajectory-orphan comparison

## Candidate Summary C6
- proposal-only next-step note:
  - if residual work continues, the next step should process `results_axis0_traj_corr_suite_v2.json` as its own bounded result-only family, while keeping the remaining ultra result-only and diagnostic/hygiene residue separate
- supporting anchors:
  - current deferred-next-source decision
