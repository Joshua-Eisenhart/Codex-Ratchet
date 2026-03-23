# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / A2-MID CONTRADICTION PRESERVATION
Batch: `BATCH_A2MID_archive_v2_packet_req_request_only_handoff__v1`
Date: 2026-03-09

- preserved contradictions:
  - summary says `a1_source packet`, yet the archive retains no inbound A1 strategy and only one outbound save packet
  - the run requests `3` steps, yet preserves only one request-emission row and zero accepted work
  - state and sidecar bind to the real inert hash `de0e5fe9...`, yet the embedded base strategy uses an all-zero input-state hash with placeholder digests
  - archived event rows still point at `system_v3/runtime/...`, while the archive-local save packet is the only preserved packet body and `sequence_state.json` is missing
- preserved non-collapse rule:
  - request emission is not earned lower-loop execution
  - packet labeling is not proof of packet-loop completion
  - archive relocation residue is not live runtime authority
