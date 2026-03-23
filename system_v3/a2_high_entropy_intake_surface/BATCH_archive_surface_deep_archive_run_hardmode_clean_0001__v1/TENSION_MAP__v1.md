# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_hardmode_clean_0001__v1`
Date: 2026-03-09

## Tension 1: Clean Park/Reject Window Versus Heavy Pending/Kill Burden
- source anchors:
  - `summary.json`
  - `state.json`
  - `HARDMODE_METRICS.json`
  - `soak_report.md`
- bounded contradiction:
  - the run reports zero parked and rejected totals and soak failure tags `NONE`, while state preserves `440` kill signals and `220` pending evidence entries and hardmode metrics still show `PARKED 440`
- intake handling:
  - keep the run as transport-clean without flattening away the large unresolved semantic burden

## Tension 2: Summary Step Count Versus Event Ledger Regime
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - summary and soak report say `100` steps/cycles, while the event ledger carries `220` result rows and step values up through `120`
- intake handling:
  - preserve as a historical counting-regime mismatch rather than trying to infer one canonical step metric

## Tension 3: Consumed Strategy Lane Versus Embedded Strategy Lane
- source anchors:
  - `a1_inbox/consumed/`
  - `zip_packets/`
- bounded contradiction:
  - both lanes contain `220` strategy packets in aligned numeric positions, but only the first aligned pair is byte-identical and the remaining `219` differ
- intake handling:
  - preserve both lanes explicitly; do not treat consumed strategy residue as a drop-in copy of the embedded transport lane

## Tension 4: Strong State Integrity Versus Missing Local Evidence Bodies
- source anchors:
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the run is hash-consistent and structurally rich, yet still references local `sim/sim_evidence_*` bodies that are absent from the archive object
- intake handling:
  - treat the run as a state/transport-heavy archive surface with incomplete evidence-body preservation

