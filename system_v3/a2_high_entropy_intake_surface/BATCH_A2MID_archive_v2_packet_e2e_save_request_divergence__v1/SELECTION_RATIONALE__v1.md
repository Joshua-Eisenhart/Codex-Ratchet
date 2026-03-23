# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
Date: 2026-03-09

## Why This Parent
- `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1` is the next untouched compact archive sibling after the mutation packet.
- it keeps the archive strip bounded while changing the contradiction shape:
  - one executed ZIPv2 cycle, then a save-request handoff instead of another executed step-result
  - final closure visible only through the request-emission row
  - same-name strategy divergence between retained and consumed lanes
  - snapshot/SIM residue richer than final machine bookkeeping
- that makes it the cleanest next archive packet after the mutation-side overhang, rather than reopening broader archive-run families.

## Bounded Goal
- reduce the parent into a smaller packet-handoff batch that preserves:
  - one executed packet cycle plus one external `A0_TO_A1_SAVE_ZIP` handoff
  - final-hash authority riding the save-request row rather than the executed step-result row
  - zero packet parks alongside parked promotion and missing canonical ledger retention
  - same-name retained-versus-consumed strategy packet divergence
  - snapshot pending-evidence and SIM kill-signal residue above empty final bookkeeping
  - runtime-path leakage and missing `sequence_state.json` as relocation residue only

## Why No Raw Source Reread
- the parent intake already retains the executed-cycle core, save-request row, final-hash split, retained-versus-consumed packet divergence, snapshot/SIM overhang, and relocation residue needed for second-pass compression
- the consulted A2-mid anchors already preserve the closest packet-identity and bookkeeping-overhang comparison surfaces

## Deferred Nearby Parents
- `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
  - best next sibling once this packet-e2e contradiction packet is preserved
- `BATCH_archive_surface_deep_archive_run_foundation_packet_failure__v1`
  - useful later for broader packet-failure comparison outside the compact ZIPv2 strip
