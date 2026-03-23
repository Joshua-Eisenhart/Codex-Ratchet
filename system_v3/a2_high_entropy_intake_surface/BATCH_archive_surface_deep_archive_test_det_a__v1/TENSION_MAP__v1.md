# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_det_a__v1`
Date: 2026-03-09

## Tension 1: Three Completed Steps Versus Two Executed Steps
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `state.json`
- bounded contradiction:
  - summary records `steps_completed 3`, while the event ledger and canonical ledger preserve only steps `1` and `2`
- intake handling:
  - preserve the third step as queued continuation state, not as executed event history

## Tension 2: Three Strategy Digests Versus Two Executed Export Digests
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - summary reports `3` unique strategy and export digests, while events preserve only `2` executed strategy/export digest pairs and the third strategy survives only as an unconsumed continuation packet
- intake handling:
  - preserve the digest surplus as replay-authored continuation residue

## Tension 3: Final Summary Hash Versus Last Event Endpoint
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - summary and state sidecar bind to `3ce0407f...`, while the last executed event ends on `232c1595...` and the queued third strategy packet uses the summary/state final hash as its input state
- intake handling:
  - preserve summary/state sidecar as the stronger final snapshot while keeping the executed event endpoint visibly distinct

## Tension 4: Empty Inbox Versus Preserved A1 Strategy Lineage
- source anchors:
  - `summary.json`
  - `a1_inbox/`
  - `zip_packets/`
- bounded contradiction:
  - summary attributes A1 source to `replay`, the inbox is empty, and all A1 lineage survives only as transport packets under `zip_packets/`
- intake handling:
  - preserve replay-authored strategy generation without inferring normal inbox delivery

## Tension 5: Zero Packet Parks Versus Three `PARKED` Promotion States
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `state.json`
- bounded contradiction:
  - summary and soak report zero parked packets, while state marks all three sim promotion statuses as `PARKED` and keeps three unresolved blockers
- intake handling:
  - preserve the distinction between packet transport cleanliness and semantic promotion closure

## Tension 6: Operator Exhaustion Versus Persisting Next-Step Proposal
- source anchors:
  - `summary.json`
  - `state.json`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - the run stops on `A2_OPERATOR_SET_EXHAUSTED`, yet a fully formed third strategy packet is still preserved as the next-step proposal
- intake handling:
  - keep the stop condition and the queued continuation together as a fail-closed boundary pair
