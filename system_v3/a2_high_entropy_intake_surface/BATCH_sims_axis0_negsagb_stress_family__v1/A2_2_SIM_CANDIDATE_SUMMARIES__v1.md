# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_axis0_negsagb_stress_family__v1`
Extraction mode: `SIM_AXIS0_NEGSAGB_STRESS_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next residual batch because the prior mutual-info baseline batch explicitly deferred this pair
- supporting anchors:
  - prior batch manifest
  - current source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - the smaller mutual-info baseline should remain comparison-only here
- supporting anchors:
  - current source membership
  - baseline comparison boundary

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “failed negativity-search surface with full-grid exhaustion and compressed retained output”
- supporting anchors:
  - `records_count = 3456`
  - `best.score = 0.0`
  - `records_sample`

## Candidate Summary C4
- proposal-only quarantine:
  - do not let the family’s search width substitute for actual negativity success
- supporting anchors:
  - zero best score
  - zero best-record branch negativity fractions

## Candidate Summary C5
- proposal-only quarantine:
  - do not assume the larger stress family outranks the smaller mutual-info baseline, because the baseline stores the stronger negativity evidence
- supporting anchors:
  - current-vs-baseline negativity comparison

## Candidate Summary C6
- proposal-only next-step note:
  - if residual pair intake continues, the next bounded family should begin at `run_axis0_sagb_entangle_seed.py`
- supporting anchors:
  - current deferred next residual-priority source
