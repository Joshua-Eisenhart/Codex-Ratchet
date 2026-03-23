# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_det_b__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_DET_B` is a compact replay-authored run that preserves two executed packet cycles, one queued third A1 continuation packet, and a nine-packet transport lattice with no inbox residue.

## Candidate Summary B
Its strongest contradiction is partial rather than total closure. Summary, soak, and events agree on `accepted 7`, `rejected 1`, and a `SCHEMA_FAIL` stop boundary, yet summary counts a third completed step and final hash `3ce0407f...` while events end after step `2` at `232c1595...`.

## Candidate Summary C
The run also preserves small packaging noise outside the active lineage. `a1_inbox/` is empty, the real strategy history lives only under `zip_packets/`, and an empty root-level `a1_strategies 2/` directory survives as residue rather than as a live strategy surface.
