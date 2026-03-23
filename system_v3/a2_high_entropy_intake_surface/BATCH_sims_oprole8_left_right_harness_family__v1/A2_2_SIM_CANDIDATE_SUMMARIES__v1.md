# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_oprole8_left_right_harness_family__v1`
Extraction mode: `SIM_OPROLE8_HARNESS_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_oprole8_left_right_suite.py` has a direct paired result and is the next unprocessed source after the history strip
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay narrow:
    - `run_oprole8_left_right_suite.py`
    - `results_oprole8_left_right_suite.json`
  - adjacent suite files should remain comparison-only
- supporting anchors:
  - direct basename pairing
  - broader suite behavior in `run_sim_suite_v1.py` and `run_sim_suite_v2_full_axes.py`

## Candidate Summary C3
- proposal-only reading:
  - the best interpretation is "fixed-role harness precursor or sibling" rather than "current evidenced operator-role suite"
- supporting anchors:
  - `run_oprole8_left_right_suite.py:1-4`
  - `SIM_CATALOG_v1.3.md:120-122`

## Candidate Summary C4
- proposal-only quarantine:
  - do not merge `oprole8` into `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` even though both sit under operator roles
- supporting anchors:
  - catalog split
  - schema and role-contract differences in this batch

## Candidate Summary C5
- proposal-only quarantine:
  - do not use the current top-level evidence-pack code hash for `S_SIM_AXIS56_OPERATOR4_LR_SUITE_V1` as a clean current provenance claim
- supporting anchors:
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:253-266`
  - current file hashes for `run_sim_suite_v1.py` and `run_sim_suite_v2_full_axes.py`

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_sim_suite_v1.py`, pair it with the result descendants it directly emits, and keep `run_sim_suite_v2_full_axes.py` separate unless source-level overlap requires bounded comparison
- supporting anchors:
  - deferred next raw-folder-order source in this batch
