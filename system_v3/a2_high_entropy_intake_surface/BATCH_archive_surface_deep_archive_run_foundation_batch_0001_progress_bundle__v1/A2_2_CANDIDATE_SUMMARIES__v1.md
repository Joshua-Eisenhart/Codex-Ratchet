# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / CANDIDATE SUMMARY SURFACE
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_PROGRESS_BUNDLE_PASS`

## Candidate Summary
- this batch classifies `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE` as a replay/export surface with three distinct retained layers: operator notes in `README_PROGRESS.txt`, a narrow embedded final snapshot of the run, and duplicated carried strategy packets
- the key contradiction is that the README preserves cumulative replay totals (`64/7/4`) while the embedded run surfaces preserve only a one-step final snapshot (`15/0/0`) sharing the same final state hash
- packet replay material is retained more broadly than replay history: seven strategy zips are carried twice and embedded once, but the short event ledger references only five of them
- the embedded state remains informative because it retains kill, park, and reject residue despite the zeroed top-line parked/rejected totals
- the bundle is useful for historical replay lineage, not for current runtime authority or full evidence retention, because it omits heavier control surfaces and drops the actual `sim/` evidence subtree
- the next bounded batch should process only `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`
