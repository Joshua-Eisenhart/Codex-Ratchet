# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_semantic_sim_0001__v1`
Date: 2026-03-09

## Tension 1: Clean Packet Counters Versus Thirty Parked Promotion States
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - packet-level surfaces report zero parks and zero rejects with top failure tag `NONE`, while state marks all thirty retained sim promotion outcomes as `PARKED`
- intake handling:
  - keep the distinction between packet cleanliness and semantic promotion state explicit

## Tension 2: Accurate Summary Accounting Versus Zero Promotion Passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `state.json`
- bounded contradiction:
  - the summary accurately matches the retained step count, accepted total, and digest diversity, yet every tier pass count stays zero and unresolved promotion blockers rise to `30`
- intake handling:
  - preserve as archive evidence that even accurate run accounting does not imply promotion success

## Tension 3: Root Sequence Ledger Present Versus Inbox Sequence Ledger Missing
- source anchors:
  - `sequence_state.json`
  - `a1_inbox/`
- bounded contradiction:
  - the global sequence ledger is retained with `A1 5`, but the inbox-local A1 sequence ledger is absent entirely
- intake handling:
  - preserve as historical retention asymmetry; do not infer an inbox-local sequence state that the archive no longer carries

## Tension 4: Embedded Strategy Naming Versus Consumed Strategy Naming
- source anchors:
  - `events.jsonl`
  - `zip_packets/`
  - `a1_inbox/consumed/`
- bounded contradiction:
  - embedded strategy packets follow a `000001` naming family while consumed residue uses a `400001` naming family, and only one consumed packet is byte-identical to an embedded packet
- intake handling:
  - preserve the naming discontinuity and the partial byte match instead of forcing one lane to stand in for the other

## Tension 5: Runtime-Like SIM Paths Versus Missing Local SIM Directory
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
  - run root inventory
- bounded contradiction:
  - retained SIM outputs point at concrete runtime `sim/sim_evidence_*` paths, yet the archived run root contains no local `sim/` directory
- intake handling:
  - preserve as structurally rich but locally incomplete evidence retention

## Tension 6: Zero Park/Reject Logs Versus Five Pending Canonical Evidence Items
- source anchors:
  - `state.json`
  - `summary.json`
- bounded contradiction:
  - state keeps no park log and no reject log, yet five canonical evidence obligations remain pending and promotion truth is still blocked
- intake handling:
  - preserve as archive evidence that evidence debt can persist without explicit park/reject residue

