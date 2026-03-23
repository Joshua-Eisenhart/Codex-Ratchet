# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005__v1`
Date: 2026-03-09

## Tension 1: Clean Packet Counters Versus Three Hundred Sixty Parked Promotion States
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - packet-level surfaces report zero parks and zero rejects with top failure tag `NONE`, while state marks all `360` retained sim promotion outcomes as `PARKED`
- intake handling:
  - keep the distinction between packet cleanliness and semantic promotion state explicit

## Tension 2: Final Snapshot Integrity Versus Event-Ledger Endpoint Drift
- source anchors:
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary, state, and sidecar agree on final hash `0045ff...`, while the last retained result row ends on `299c9c...`
- intake handling:
  - preserve the stronger snapshot binding without pretending the event ledger alone closes the run

## Tension 3: Deterministic Replay Versus Divergent Replay Final Hash
- source anchors:
  - `REPLAY_AUDIT.json`
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - replay audit says determinism `pass true`, yet its replay final hash `ed1a34...` does not match the summary/state final hash `0045ff...`
- intake handling:
  - preserve replay audit as a historical derivative audit layer, not as a superior authority surface

## Tension 4: Replay Coverage Versus Replay Failure Texture
- source anchors:
  - `REPLAY_AUDIT.json`
  - `zip_packets/`
- bounded contradiction:
  - replay covers the full `541` packet lattice one-for-one, but only `60` events replay `OK` and `481` replay as `PARK`
- intake handling:
  - preserve the replay audit as failure-rich structural evidence rather than clean validation proof

## Tension 5: Root Sequence Ledger Present Versus Inbox Sequence Ledger Missing
- source anchors:
  - `sequence_state.json`
  - `a1_inbox/`
- bounded contradiction:
  - the global sequence ledger is retained with `A1 60`, but the inbox-local A1 sequence ledger is absent entirely
- intake handling:
  - preserve as historical retention asymmetry; do not infer an inbox-local sequence state that the archive no longer carries

## Tension 6: Embedded Strategy Naming Versus Consumed Strategy Naming
- source anchors:
  - `events.jsonl`
  - `zip_packets/`
  - `a1_inbox/consumed/`
- bounded contradiction:
  - embedded strategy packets follow a `000001` naming family while consumed residue uses a `400001` naming family, and fifty-nine of sixty same-position pairs differ byte-for-byte
- intake handling:
  - preserve the naming discontinuity and dominant byte mismatch instead of forcing one lane to stand in for the other

## Tension 7: Runtime-Like SIM Paths Versus Missing Local SIM Directory
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
  - run root inventory
- bounded contradiction:
  - retained SIM outputs point at concrete runtime `sim/sim_evidence_*` paths, yet the archived run root contains no local `sim/` directory
- intake handling:
  - preserve as structurally rich but locally incomplete evidence retention

## Tension 8: Signal Audit Null Field Versus Nonzero Kill Math Metadata
- source anchors:
  - `SIGNAL_AUDIT.json`
- bounded contradiction:
  - the compact audit surface reports `MATH_DEF 120` inside `kill_kind_counts`, yet `killed_math_count` is `null`
- intake handling:
  - preserve as an unresolved audit-surface nullability seam instead of backfilling a count from adjacent fields
