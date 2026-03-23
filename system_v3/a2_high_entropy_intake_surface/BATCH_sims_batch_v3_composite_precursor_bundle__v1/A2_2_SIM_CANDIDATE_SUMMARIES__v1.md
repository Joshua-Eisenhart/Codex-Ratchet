# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
Extraction mode: `SIM_BATCH_BUNDLE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_batch_v3.py` and `results_batch_v3.json` form one self-contained composite precursor package
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the most reusable fact from this batch is not any one embedded metric, but the packaging pattern:
    - one runner
    - four embedded SIM_ID payloads
    - one aggregate result file
    - per-payload evidence hashes
- supporting anchors:
  - `run_batch_v3.py:416-500`
  - `results_batch_v3.json:1-222`

## Candidate Summary C3
- proposal-only reading:
  - the strongest current repo-local interpretation is that `batch_v3` has been superseded by decomposed standalone descendant surfaces rather than preserved as a first-class current evidence surface
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:39-54`
  - `SIM_CATALOG_v1.3.md:102-108`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:2-40`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-414`

## Candidate Summary C4
- proposal-only quarantine:
  - do not claim exact one-to-one identity between the bundle payloads and later standalone descendants; the schemas and stored revisions drift by family
- supporting anchors:
  - descendant result surfaces read in this batch

## Candidate Summary C5
- proposal-only quarantine:
  - do not merge adjacent `engine32_axis0_axis6_attack` into this batch on the basis of shared axis vocabulary alone
- supporting anchors:
  - `run_engine32_axis0_axis6_attack.py`
  - `results_engine32_axis0_axis6_attack.json`
  - catalog placement comparison

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_engine32_axis0_axis6_attack.py` with its paired result and test whether `run_full_axis_suite.py` is structurally same-family or only nearby in raw order
- supporting anchors:
  - adjacent raw-order source comparison in this batch
