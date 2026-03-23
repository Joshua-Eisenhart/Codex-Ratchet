# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_full_axis_suite_sampler_family__v1`
Extraction mode: `SIM_FULL_AXIS_SAMPLER_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_full_axis_suite.py` and `results_full_axis_suite.json` form one self-contained cross-axis sampler surface
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the strongest interpretation here is “precursor sampler that points toward later standalone descendants,” not “current direct producer of those descendants”
- supporting anchors:
  - `results_full_axis_suite.json`
  - catalog and evidence-pack comparisons in this batch

## Candidate Summary C3
- proposal-only reading:
  - continuity strength is uneven:
    - Axis3 is the closest descendant class
    - Axis4 is the most visibly divergent
    - Axis5 FSA stays near-zero across versions
- supporting anchors:
  - sampler and descendant result surfaces read in this batch

## Candidate Summary C4
- proposal-only quarantine:
  - do not equate the sampler’s emitted SIM_ID names with the current standalone descendant names without preserving rename and hash drift
- supporting anchors:
  - `run_full_axis_suite.py:245-250`
  - catalog/evidence anchors in this batch

## Candidate Summary C5
- proposal-only quarantine:
  - do not infer that the sampler hash `71aa883f...` is a current evidenced producer path for the descendant surfaces
- supporting anchors:
  - sampler hash and descendant evidence-pack code hashes in this batch

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_history_invariant_gradient_scan_v11.py`, pair it with `results_history_invariant_gradient_scan_v11.json`, and determine whether the nearby history-order scan files belong to the same bounded family
- supporting anchors:
  - deferred next raw-folder-order source in this batch
