# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_det_a__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_DET_A` is a compact replay-authored run that preserves two executed packet cycles, one queued third A1 continuation packet, and a nine-packet transport lattice with no inbox residue.

## Candidate Summary B
Its strongest contradiction is not total incoherence but partial closure. Summary, soak, and events agree on `accepted 7`, `rejected 1`, and a `SCHEMA_FAIL` stop boundary, yet summary counts a third completed step and final hash `3ce0407f...` while events end after step `2` at `232c1595...`.

## Candidate Summary C
The run is transport-clean but semantically unfinished. No packet parks are recorded, but state still keeps three `PARKED` sim promotion states, three unresolved blockers, and one schema-fail reject while a fully formed third strategy packet remains queued.
