# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - summary and soak surfaces collapse the run to zero accepted work
  - state and events retain accepted packet history, rejected residue, and parked sim promotion states
- contradiction 2:
  - summary says one step completed
  - state canonical ledger preserves step `1` and step `2`
- contradiction 3:
  - `sequence_state.json` zeros all source lanes
  - the run root still visibly retains one packet in each active lane
- contradiction 4:
  - all three strategy zip copies share one filename
  - inbox/consumed copies are identical invalid payloads while the transport-lane copy is different, larger, and richer
- contradiction 5:
  - the packet lattice preserves one accepted export/snapshot/SIM path
  - repeated fail rows and reject log preserve later schema-fail regeneration at the same step
- contradiction 6:
  - summary/state sidecar align on one final hash
  - duplicated success rows end on another hash and the transport-lane strategy packet points back to an earlier prior-state hash

## Preservation Rule
- none of the contradictions above are resolved in this batch
- the reduction narrows them into reusable archive-side fences without collapsing them into one consistent execution story

