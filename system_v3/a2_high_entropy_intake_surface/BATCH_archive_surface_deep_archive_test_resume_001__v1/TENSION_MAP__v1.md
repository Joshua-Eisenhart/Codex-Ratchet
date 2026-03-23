# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_resume_001__v1`
Date: 2026-03-09

## Tension 1: One-Step Summary Versus Two Emitted Save Requests
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `zip_packets/`
- bounded contradiction:
  - summary says `steps_completed 1` and `steps_requested 1`, yet the event ledger preserves two `a1_strategy_request_emitted` rows and the packet lattice keeps two outbound save zips
- intake handling:
  - preserve the duplicate external request emission without inventing a missing second step

## Tension 2: Both Event Rows Stay At `step 1` While Packet Sequence Advances To `2`
- source anchors:
  - `events.jsonl`
  - both `ZIP_HEADER.json` members
  - both `A0_SAVE_SUMMARY.json` members
- bounded contradiction:
  - the event ledger keeps `step 1` for both rows, the second packet header advances to `sequence 2`, and both save summaries still report `step 1`
- intake handling:
  - preserve event-step and packet-sequence drift as a real historical seam in the resume handoff

## Tension 3: Archived Run Object Versus Active-Runtime Packet Paths
- source anchors:
  - `events.jsonl`
  - archive-local `zip_packets/`
- bounded contradiction:
  - the retained event rows reference live-runtime packet paths under `system_v3/runtime/...`, while the preserved packet bodies now live in the archive mirror
- intake handling:
  - preserve the path leakage as historical provenance residue rather than rewriting it to archive-local paths

## Tension 4: Run-Specific Outer State Hash Versus Zeroed Inner Strategy Input
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `A0_SAVE_SUMMARY.json`
- bounded contradiction:
  - summary/state sidecar and top-level save summary all bind to `de0e5fe9...`, while the embedded `base_strategy.inputs.state_hash` is all zeroes
- intake handling:
  - preserve the layered mismatch between outer run identity and inner sample strategy scaffold

## Tension 5: Packet-Sourced External Strategy Stop Versus No Inbound Strategy Surface
- source anchors:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`
- bounded contradiction:
  - summary says `a1_source packet` and `A1_NEEDS_EXTERNAL_STRATEGY`, but no inbound A1 packet survives locally; only outbound A0-to-A1 save zips remain
- intake handling:
  - preserve the run as an external-handoff stub, not as evidence that the inbound strategy ever returned

## Tension 6: Generic Sample Strategy Versus Run-Specific Resume Shell
- source anchors:
  - `A0_SAVE_SUMMARY.json`
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - the archived run is specific to `TEST_RESUME_001`, but the retained save payload is a generic `STRAT_SAMPLE_0001` scaffold with placeholder digest fields and fixed sample bind names
- intake handling:
  - preserve the payload as sample/placeholder residue rather than treating it as earned strategy output
