# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_archive_v2_packet_req_request_only_handoff__v1`
Date: 2026-03-09

- selected parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
- why this parent:
  - it was the first actually unresolved compact archive-side sibling after the already-covered chain-B, mutation, and ZIPv2 packet-e2e packets
  - it is smaller and cleaner than `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
  - it preserves a distinct request-only contradiction surface rather than another executed multi-step replay lattice
- comparison anchors used:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
- bounded reduction goal:
  - preserve request-only handoff boundaries, packet-label contradiction, planned-step overhang, outer-versus-embedded hash split, and relocation residue without promoting any of it into runtime or transport authority
- explicit non-goals:
  - no raw source reread
  - no active A2 append-save
  - no packet-law generalization from this archive object alone
