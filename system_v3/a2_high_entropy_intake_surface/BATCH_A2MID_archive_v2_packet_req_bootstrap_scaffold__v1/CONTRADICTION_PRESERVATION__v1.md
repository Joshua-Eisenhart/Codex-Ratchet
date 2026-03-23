# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - summary labels the run `packet`
  - the archive keeps no inbound A1 strategy, no strategy/export digests, and only one outbound save packet
- contradiction 2:
  - the run requests `3` steps
  - only one retained row survives and it is already an immediate `a1_strategy_request_emitted` handoff with zero accepted work
- contradiction 3:
  - final state is inert with zero accepted, survivor, SIM, evidence, and canonical-ledger counts
  - lexical/bootstrap shells still remain populated
- contradiction 4:
  - state and outer save summary bind to real hash `de0e5fe9...`
  - the embedded base strategy uses an all-zero input-state hash and placeholder self-audit values
- contradiction 5:
  - the archive keeps a local save packet copy
  - the retained event row still points to a runtime-local packet path and the run root lacks `sequence_state.json`

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into a clean packet-loop story, a clean three-step story, or a clean earned-state story
