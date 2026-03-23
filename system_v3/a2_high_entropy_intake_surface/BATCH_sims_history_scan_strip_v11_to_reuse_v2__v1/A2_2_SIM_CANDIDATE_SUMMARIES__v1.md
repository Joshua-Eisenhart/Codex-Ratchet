# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_history_scan_strip_v11_to_reuse_v2__v1`
Extraction mode: `SIM_HISTORY_STRIP_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because the history and reuse scripts form one contiguous strip beginning at `run_history_invariant_gradient_scan_v11.py`
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the best family read is "executable strip with partial storage" rather than "uniformly evidenced history cluster"
- supporting anchors:
  - eleven script members versus one result surface

## Candidate Summary C3
- proposal-only reading:
  - `v11` should remain the anchor pair for this batch, but only with an explicit quarantine around the current runner / stored result mismatch
- supporting anchors:
  - `run_history_invariant_gradient_scan_v11.py`
  - `results_history_invariant_gradient_scan_v11.json`

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat `run_history_variant_order_preserved_v13.py` as a clean executable coordinator because it includes itself in its launch list
- supporting anchors:
  - `run_history_variant_order_preserved_v13.py:1-19`

## Candidate Summary C5
- proposal-only quarantine:
  - do not infer evidence-pack admission for the strip from catalog visibility or from local console-print behavior
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:104`
  - search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_oprole8_left_right_suite.py` and determine its nearest result/evidence siblings without merging it into the history strip
- supporting anchors:
  - deferred next raw-folder-order source in this batch
