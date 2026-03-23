# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
Date: 2026-03-09

## Candidate Summary A
`TEST_STATE_TRANSITION_MUTATION` is a compact one-step mutation run with one executed strategy/export/snapshot spine, two retained SIM returns, no queued continuation packet, and a final retained state that sits above the only event row.

## Candidate Summary B
Its strongest contradiction is closure mismatch rather than transport failure. Summary and state sidecar bind to `63995c34...`, while the sole executed event ends on `fcb5d2fe...`; summary and soak also report zero parks and zero rejects while final state keeps two `PARKED` promotion states and two unresolved blockers.

## Candidate Summary C
The human-readable and packet-facing surfaces are richer than the final bookkeeping layer. The snapshot still lists pending evidence for both retained specs, export and snapshot both preserve `KILL_IF ... NEG_NEG_BOUNDARY` lines, final state keeps both `evidence_pending` and `kill_log` empty, and the root also carries exact duplicate ` 2` files plus empty residue directories.
