# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
Extraction mode: `SIM_STAGE16_SUB4_AXIS6U_ABSOLUTE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_stage16_sub4_axis6u.py` is the next unprocessed entrypoint and has one direct paired result surface
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - the mixed-axis6 family and the terrain-only suite should remain comparison-only here
- supporting anchors:
  - batch selection and structural map

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “absolute Stage16 baseline family with local-only SIM_ID admission and sibling top-level descendant relatives”
- supporting anchors:
  - current runner contract
  - V4 / V5 comparison seam

## Candidate Summary C4
- proposal-only quarantine:
  - do not infer repo-top evidence strength for `S_SIM_STAGE16_SUB4_AXIS6U` from the presence of Stage16 V4 / V5 descendant blocks
- supporting anchors:
  - negative search for `S_SIM_STAGE16_SUB4_AXIS6U`
  - positive V4 / V5 blocks

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge `stage16_sub4_axis6u` with the mixed-axis6 family just because its values match the control `U_*` baseline up to floating-point noise
- supporting anchors:
  - control-baseline comparison
  - current absolute-only contract

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_terrain8_sign_suite.py`, pair it with `results_terrain8_sign_suite.json`, and map it as a terrain-only sign family rather than as Stage16 carryover
- supporting anchors:
  - deferred next raw-folder-order source in this batch
