# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis0_mi_discrim_branches_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior residual paired-family batch explicitly deferred this pair
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - the `_ab` sibling should remain comparison-only here
- supporting anchors:
  - current source membership
  - sibling contract boundary

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “non-AB control branch family with a compact `SAgB` split and machine-scale MI layer”
- supporting anchors:
  - current result metrics
  - current runner contract

## Candidate Summary C4
- proposal-only quarantine:
  - do not describe the current family as a meaningful MI discriminator without qualification
- supporting anchors:
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 1.951563910473908e-18`

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge the current family with `run_axis0_mi_discrim_branches_ab.py`, because the sibling AB coupling materially changes the stored behavior
- supporting anchors:
  - sibling CNOT insertion
  - sibling nonzero MI metrics

## Candidate Summary C6
- proposal-only next-step note:
  - if residual pair intake continues, the next bounded family should begin at `run_axis0_mi_discrim_branches_ab.py`
- supporting anchors:
  - current deferred next residual-priority source
