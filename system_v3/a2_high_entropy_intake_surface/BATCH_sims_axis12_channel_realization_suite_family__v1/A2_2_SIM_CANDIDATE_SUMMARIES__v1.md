# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis12_channel_realization_suite_family__v1`
Extraction mode: `SIM_AXIS12_CHANNEL_REALIZATION_SUITE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior axis0 trajectory-suite batch explicitly deferred this pair
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - the adjacent harden scripts should remain deferred to the runner-only residual class
- supporting anchors:
  - current source membership
  - raw folder order and missing paired results for the harden scripts

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “fixed-parameter axis12 realization suite where `SEQ02` is locally best and the edge partition is only a coarse classifier”
- supporting anchors:
  - current edge flags
  - current endpoint metrics

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat the local suite SIM_ID as repo-top admitted just because `V4` shares the same runner hash
- supporting anchors:
  - current runner hash
  - top-level evidence-pack `V4` block

## Candidate Summary C5
- proposal-only quarantine:
  - do not collapse the local fixed-parameter suite into the repo-top `V4` grid scan, because the admitted descendant is broader in parameter space and different in surface shape
- supporting anchors:
  - local result structure
  - `V4` grid structure

## Candidate Summary C6
- proposal-only next-step note:
  - if residual pair intake continues, the next bounded family should begin at `run_axis12_seq_constraints.py`
- supporting anchors:
  - current deferred next residual-priority source
