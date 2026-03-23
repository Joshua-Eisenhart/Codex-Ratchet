# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_SUITE_V2_ORPHAN_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior boundary/bookkeep orphan explicitly deferred `results_axis0_traj_corr_suite_v2.json` next
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at one source member, because the current best read is “standalone result-only orphan related to but not merged with the local traj-corr family”
- supporting anchors:
  - current source membership
  - current local-family comparison

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “compressed seq01-baseline-plus-deltas successor/orphan with hidden `T1`/`T2` axis and strongest perturbation on `T1_REV_BELL_CNOT_R1_SEQ04`”
- supporting anchors:
  - current lattice read
  - current extrema

## Candidate Summary C4
- proposal-only quarantine:
  - do not infer a present runner from family resemblance, because no direct `traj_corr_suite_v2` runner-name hit exists in current `simpy/`
- supporting anchors:
  - current `simpy/` inventory check

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge the current orphan into the earlier local suite or into `V4` / `V5`, because all three contracts differ materially
- supporting anchors:
  - current local-family comparison
  - current descendant comparison

## Candidate Summary C6
- proposal-only next-step note:
  - if residual work continues, the next step should process `results_ultra3_full_geometry_stage16_axis0.json`, deciding separately whether `results_ultra_big_ax012346.json` belongs in the same bounded ultra family
- supporting anchors:
  - current deferred-next-source decision
