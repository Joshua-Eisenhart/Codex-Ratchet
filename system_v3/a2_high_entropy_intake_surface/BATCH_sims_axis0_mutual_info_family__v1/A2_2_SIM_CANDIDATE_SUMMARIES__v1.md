# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis0_mutual_info_family__v1`
Extraction mode: `SIM_AXIS0_MUTUAL_INFO_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior AB branch batch explicitly deferred this pair
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - the adjacent stress sweep should remain comparison-only here
- supporting anchors:
  - current source membership
  - next-family boundary

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “minimal Ginibre MI baseline that barely clears its own local negativity kill gate”
- supporting anchors:
  - current result metrics
  - runner kill-gate logic

## Candidate Summary C4
- proposal-only quarantine:
  - do not equate the current robustly positive MI statistics with a strong negativity result
- supporting anchors:
  - `MI_mean = 0.2724236385732822`
  - `neg_SAgB_frac = 0.001953125`

## Candidate Summary C5
- proposal-only quarantine:
  - do not assume the larger `negsagb_stress` sweep supersedes this baseline, because its stored best score is zero
- supporting anchors:
  - current-vs-stress negativity comparison

## Candidate Summary C6
- proposal-only next-step note:
  - if residual pair intake continues, the next bounded family should begin at `run_axis0_negsagb_stress.py`
- supporting anchors:
  - current deferred next residual-priority source
