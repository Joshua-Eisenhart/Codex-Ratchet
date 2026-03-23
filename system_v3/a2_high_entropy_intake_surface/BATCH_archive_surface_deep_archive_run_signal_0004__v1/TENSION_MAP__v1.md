# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0004__v1`
Date: 2026-03-09

## Tension 1: Forty-Step Summary Versus Sixty Retained A1 Passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `state.json`
  - `sequence_state.json`
- bounded contradiction:
  - `summary.json` says `steps_completed 40`, while `events.jsonl` keeps `60` result rows, `state.json` keeps `accepted_batch_count 60`, and `sequence_state.json` ends with `A1 60`
- intake handling:
  - preserve as compressed summary-over-transport history rather than normalizing everything to one step count

## Tension 2: Accurate Visible Summary Counters Versus Underreported Accepted Flow
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - summary and soak both report `accepted_total 640`, while the retained event rows add to `960` because steps `1` through `20` each appear twice
- intake handling:
  - preserve the duplicate-row compression explicitly; do not smooth the event lattice back down to summary totals

## Tension 3: Clean Packet Counters Versus Three Hundred Sixty Parked Promotion States
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - packet-level surfaces report zero parks and zero rejects with top failure tag `NONE`, while state marks all `360` retained sim promotion outcomes as `PARKED`
- intake handling:
  - keep the distinction between packet cleanliness and semantic promotion state explicit

## Tension 4: Final Snapshot Integrity Versus Event-Ledger Endpoint Drift
- source anchors:
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary, state, and sidecar agree on final hash `6e07a4...`, while the last retained result row ends on `d08f6d...`
- intake handling:
  - preserve the stronger snapshot binding without pretending the event ledger alone closes the run

## Tension 5: Deterministic Replay Versus Divergent Replay Final Hash
- source anchors:
  - `REPLAY_AUDIT.json`
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - replay audit says determinism `pass true`, yet its replay final hash `e840db...` does not match the summary/state final hash `6e07a4...`
- intake handling:
  - preserve replay audit as a historical derivative audit layer, not as a superior authority surface

## Tension 6: Replay Coverage Versus Replay Failure Texture
- source anchors:
  - `REPLAY_AUDIT.json`
  - `zip_packets/`
- bounded contradiction:
  - replay covers the full `541` packet lattice one-for-one, but only `60` events replay `OK` and `481` replay as `PARK`
- intake handling:
  - preserve the replay audit as failure-rich structural evidence rather than clean validation proof

## Tension 7: Root Sequence Ledger Present Versus Inbox Sequence Ledger Missing
- source anchors:
  - `sequence_state.json`
  - `a1_inbox/`
- bounded contradiction:
  - the global sequence ledger is retained with `A1 60`, but the inbox-local A1 sequence ledger is absent entirely
- intake handling:
  - preserve as historical retention asymmetry; do not infer an inbox-local sequence state that the archive no longer carries

## Tension 8: Embedded Strategy Naming Versus Consumed Strategy Naming
- source anchors:
  - `events.jsonl`
  - `zip_packets/`
  - `a1_inbox/consumed/`
- bounded contradiction:
  - embedded strategy packets follow a `000001` naming family while consumed residue uses a `400001` naming family, and fifty-nine of sixty same-position pairs differ byte-for-byte
- intake handling:
  - preserve the naming discontinuity and dominant byte mismatch instead of forcing one lane to stand in for the other

## Tension 9: Runtime-Like SIM Paths Versus Missing Local SIM Directory
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
  - run root inventory
- bounded contradiction:
  - retained SIM outputs point at concrete runtime `sim/sim_evidence_*` paths, yet the archived run root contains no local `sim/` directory
- intake handling:
  - preserve as structurally rich but locally incomplete evidence retention
