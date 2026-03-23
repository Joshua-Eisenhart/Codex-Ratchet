# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_resume_001__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_RESUME_001` is a zero-work external-handoff run: it stops at `A1_NEEDS_EXTERNAL_STRATEGY`, retains no accepted or rejected lower-loop work, and preserves only two outbound `A0_TO_A1_SAVE_ZIP` packets plus an empty inbox.

## Candidate Summary B
Its strongest contradiction is duplicated request emission inside a one-step shell. Summary says one step, both event rows still say `step 1`, but the archive keeps two outbound save requests and a packet header sequence that advances from `1` to `2`.

## Candidate Summary C
The preserved save payload is generic rather than earned. Both save zips carry the same `A0_SAVE_SUMMARY.json` with `STRAT_SAMPLE_0001`, placeholder digest fields, and an inner all-zero input state hash, while the outer save summary and final run state bind to the real hash `de0e5fe9...`; the event ledger also still points to active-runtime absolute paths instead of the archive mirror.
