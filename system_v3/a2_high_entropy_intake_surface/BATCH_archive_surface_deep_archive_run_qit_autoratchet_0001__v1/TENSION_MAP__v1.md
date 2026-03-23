# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0001__v1`
Date: 2026-03-09

## Tension 1: Zero-Accept Headline Versus Accepted First Step
- source anchors:
  - `summary.json`
  - `state.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - summary and soak report say `accepted_total 0`, while state keeps one accepted batch and the event ledger preserves a step-result row with `accepted 7`
- intake handling:
  - preserve both surfaces without collapsing the run into either "zero-accept" or "fully successful"

## Tension 2: Sequence Ledger Versus Sequence-Gap Failure
- source anchors:
  - `sequence_state.json`
  - `events.jsonl`
  - `a1_inbox/`
- bounded contradiction:
  - the run retains an explicit sequence ledger and still fails four times on `SEQUENCE_GAP` while packets `000002` through `000005` remain queued
- intake handling:
  - preserve as archive evidence that explicit sequence tracking did not prevent queue-gap failure in this run

## Tension 3: Zero Packet Parks Versus Parked Sim Outcomes
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - packet-level surfaces report zero parks and zero rejects, while state marks both sims as `PARKED` and retains one pending canonical evidence item
- intake handling:
  - keep the distinction between packet transport cleanliness and semantic promotion state

## Tension 4: Same Filename Versus Different Strategy Bytes
- source anchors:
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - the consumed and embedded strategy surfaces preserve different byte payloads under the same packet filename
- intake handling:
  - preserve both as separate historical surfaces; do not infer equivalence from filename alone

## Tension 5: Strong State Integrity Versus Missing Evidence Bodies
- source anchors:
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - final-state integrity is strong, but the archive still omits the local `sim/sim_evidence_*` texts referenced by the event and soak surfaces
- intake handling:
  - treat the run as a structurally useful archive surface with incomplete evidence-body retention

