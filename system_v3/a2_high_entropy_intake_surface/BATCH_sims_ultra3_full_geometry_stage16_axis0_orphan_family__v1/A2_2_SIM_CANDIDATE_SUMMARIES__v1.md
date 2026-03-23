# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
Extraction mode: `SIM_ULTRA3_FULL_GEOMETRY_STAGE16_AXIS0_ORPHAN_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior axis0 traj-corr v2 orphan explicitly deferred `results_ultra3_full_geometry_stage16_axis0.json` next
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at one source member, because the current best read is “standalone result-only ultra seam surface with no admitted runner”
- supporting anchors:
  - current source membership
  - current evidence visibility read

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “geometry-bearing ultra orphan with `stage16` plus `axis0_ab`, exact sign-symmetric berry flux at stored precision, and strongest `axis0_ab` delta on `T1_REV_BELL_CNOT_R1_SEQ04`”
- supporting anchors:
  - current structural map
  - current extrema

## Candidate Summary C4
- proposal-only quarantine:
  - do not collapse the current orphan into ultra4 or the final ultra sweep, because it shares only part of each contract
- supporting anchors:
  - current ultra-strip comparisons

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge `results_ultra_big_ax012346.json` into this batch, because its topology-plus-traj contract is materially different
- supporting anchors:
  - current `ultra_big` separation read

## Candidate Summary C6
- proposal-only next-step note:
  - if residual work continues, the next step should process `results_ultra_big_ax012346.json` as its own bounded ultra result-only family
- supporting anchors:
  - current deferred-next-source decision
