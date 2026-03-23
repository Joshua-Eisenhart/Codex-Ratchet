# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0002__v1`
Date: 2026-03-09

## Tension 1: Clean Packet Counters Versus Three Hundred Parked Promotion States
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - packet-level surfaces report zero parks and zero rejects with top failure tag `NONE`, while state marks all three hundred retained sim promotion outcomes as `PARKED`
- intake handling:
  - keep the distinction between packet cleanliness and semantic promotion state explicit

## Tension 2: Accurate Summary Accounting Versus Zero Promotion Passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `state.json`
- bounded contradiction:
  - the summary accurately matches the retained step count, accepted total, and digest diversity, yet every tier pass count stays zero and unresolved promotion blockers rise to `300`
- intake handling:
  - preserve as archive evidence that accurate run accounting does not imply promotion success

## Tension 3: Final Snapshot Integrity Versus Event-Ledger Endpoint Drift
- source anchors:
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary, state, and sidecar agree on final hash `3d779f...`, while the last retained result row ends on `496d384...`
- intake handling:
  - preserve the stronger snapshot binding without pretending the event ledger alone closes the run

## Tension 4: Root Sequence Ledger Present Versus Inbox Sequence Ledger Missing
- source anchors:
  - `sequence_state.json`
  - `a1_inbox/`
- bounded contradiction:
  - the global sequence ledger is retained with `A1 50`, but the inbox-local A1 sequence ledger is absent entirely
- intake handling:
  - preserve as historical retention asymmetry; do not infer an inbox-local sequence state that the archive no longer carries

## Tension 5: Embedded Strategy Naming Versus Consumed Strategy Naming
- source anchors:
  - `events.jsonl`
  - `zip_packets/`
  - `a1_inbox/consumed/`
- bounded contradiction:
  - embedded strategy packets follow a `000001` naming family while consumed residue uses a `400001` naming family, and forty-nine of fifty same-position pairs differ byte-for-byte
- intake handling:
  - preserve the naming discontinuity and the dominant byte mismatch instead of forcing one lane to stand in for the other

## Tension 6: Runtime-Like SIM Paths Versus Missing Local SIM Directory
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
  - run root inventory
- bounded contradiction:
  - retained SIM outputs point at concrete runtime `sim/sim_evidence_*` paths, yet the archived run root contains no local `sim/` directory
- intake handling:
  - preserve as structurally rich but locally incomplete evidence retention

## Tension 7: Zero Park/Reject Logs Versus Fifty Pending Canonical Evidence Items
- source anchors:
  - `state.json`
  - `summary.json`
- bounded contradiction:
  - state keeps no park log and no reject log, yet fifty canonical evidence obligations remain pending and promotion truth is still blocked
- intake handling:
  - preserve as archive evidence that evidence debt can persist without explicit park/reject residue
