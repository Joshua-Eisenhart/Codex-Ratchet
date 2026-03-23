# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
Date: 2026-03-09

## Tension 1: Zero-Accept Summary Versus Accepted State And Event Residue
- source anchors:
  - `summary.json`
  - `state.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - summary and soak report both report zero accepted work, while state keeps two accepted batches and the event ledger preserves three success rows totaling six accepted items
- intake handling:
  - preserve summary collapse and deeper-state over-retention side by side

## Tension 2: One-Step Run Versus Two-Step Canonical Ledger
- source anchors:
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - summary reports `steps_completed 1`, while state canonical ledger records step `1` and step `2` with sequences `1` and `2`
- intake handling:
  - preserve the ledger as retained state history without promoting it over the explicit run summary

## Tension 3: Visible Packet Lattice Versus Zeroed Sequence Ledger
- source anchors:
  - `sequence_state.json`
  - `zip_packets/`
- bounded contradiction:
  - `sequence_state.json` zeros every source lane even though the run root visibly retains one packet for A1, A0->B, B, and SIM
- intake handling:
  - treat the sequence ledger as flattened residue, not as authoritative packet absence

## Tension 4: Same-Named Strategy Packet Versus Different Bytes And Validity
- source anchors:
  - `a1_inbox/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - all three copies share the same packet name, but the inbox and consumed copies are identical invalid payloads while the transport-lane copy is a different, richer payload
- intake handling:
  - preserve location-dependent packet identity instead of collapsing by filename

## Tension 5: Accepted Packet Spine Versus Fail-Closed Regeneration Noise
- source anchors:
  - `events.jsonl`
  - export/state-update/SIM packet payloads
  - inbox strategy packet payload
  - `state.json`
- bounded contradiction:
  - export, snapshot, and SIM packets preserve one accepted baseline path, while repeated fail rows and the reject log preserve later schema failure at the same step
- intake handling:
  - keep both layers: accepted packet spine as historical execution and fail-closed regeneration as later contradictory residue

## Tension 6: Summary Final Hash Versus Event Endpoint Hash
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary and sidecar bind to `aed8327f...`, while all duplicated success rows end on `3aede158...`
- intake handling:
  - preserve summary/state sidecar as the stronger snapshot binding without pretending the event endpoint agrees

## Tension 7: A1 Source `packet` Versus Repeated A1 Packet Schema Failure
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - inbox strategy packet payload
- bounded contradiction:
  - summary says A1 source is `packet`, yet the retained A1 packet copies in inbox and consumed are schema-invalid and the event ledger repeats that schema-fail twenty-nine times
- intake handling:
  - preserve `a1_source` as metadata only, not as proof that the retained inbox copy was valid
