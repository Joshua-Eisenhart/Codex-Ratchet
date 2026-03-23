# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_resume_stub_leakage__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - summary says one completed/requested step
  - the archive retains two `a1_strategy_request_emitted` rows and two outbound save packets
- contradiction 2:
  - both event rows remain at `step 1`
  - the second packet header advances to `sequence 2`
- contradiction 3:
  - the run is now an archive object
  - event rows still point to live-runtime absolute packet paths
- contradiction 4:
  - summary/state sidecar and top-level save summary bind to real hash `de0e5fe9...`
  - the embedded base strategy uses an all-zero input state hash
- contradiction 5:
  - summary says `a1_source packet` and stop reason `A1_NEEDS_EXTERNAL_STRATEGY`
  - no inbound A1 strategy packet survives locally; only outbound save zips remain
- contradiction 6:
  - operational state collapses to zero
  - lexical shell surfaces remain populated

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into a clean inbound return story, a clean two-step story, or a trusted payload-provenance story

