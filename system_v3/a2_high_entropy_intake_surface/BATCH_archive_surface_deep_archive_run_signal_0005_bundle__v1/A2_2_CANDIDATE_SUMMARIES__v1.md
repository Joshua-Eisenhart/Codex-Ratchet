# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1`
Date: 2026-03-09

## Candidate Summary A
This archive object is a self-contained signal export bundle with one embedded `RUN_SIGNAL_0005/` root, `1271` file members, `360` local sim evidence files, `60` strategy JSONs, `60` outbox export blocks, `60` snapshots, `120` compile/eval reports, the full `541` packet lattice, and the dual audit overlays.

## Candidate Summary B
The strongest contradiction is not runtime-count drift but closure divergence under fuller retention. Embedded summary, state, sequence, soak, and event rows all agree on sixty passes and nine hundred sixty accepted items, yet the final snapshot hash, event-lattice endpoint hash, and deterministic replay final hash are still all different.

## Candidate Summary C
The bundle is transport-clean but semantically burdened. No packet parks or rejects are recorded in the runtime-facing summaries, yet embedded final state keeps sixty pending canonical evidence items and three hundred sixty `PARKED` sim promotion states, while the replay audit marks only sixty events `OK` and four hundred eighty-one `PARK`.
