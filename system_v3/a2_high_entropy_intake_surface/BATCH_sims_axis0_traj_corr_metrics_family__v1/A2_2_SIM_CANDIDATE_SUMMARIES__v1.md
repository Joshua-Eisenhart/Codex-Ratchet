# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis0_traj_corr_metrics_family__v1`
Extraction mode: `SIM_AXIS0_TRAJ_CORR_METRICS_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior Bell-seed batch explicitly deferred this pair
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - the next trajectory-suite pair should remain deferred
- supporting anchors:
  - current source membership
  - deferred next residual-priority source

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “dual-init trajectory-correlation surface with Bell-only stored trajectory negativity and Ginibre-only stored nonnegativity”
- supporting anchors:
  - current result metrics
  - current runner contract

## Candidate Summary C4
- proposal-only quarantine:
  - do not mistake Bell trajectory negativity for negative final-state conditional entropy, because all stored final `SAgB` means are positive
- supporting anchors:
  - current Bell final-state metrics
  - current Bell negativity-fraction metrics

## Candidate Summary C5
- proposal-only quarantine:
  - do not treat the sequence-order effect as globally signed, because the delta direction flips between Bell and Ginibre initialization
- supporting anchors:
  - init-specific delta metrics in the current result

## Candidate Summary C6
- proposal-only next-step note:
  - if residual pair intake continues, the next bounded family should begin at `run_axis0_traj_corr_suite.py`
- supporting anchors:
  - current deferred next residual-priority source
