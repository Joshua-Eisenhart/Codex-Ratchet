# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_bundle__v1`
Date: 2026-03-09

## Tension 1: Clean Headline Versus Retained Kill Signals
- source anchors:
  - `README_WORKING_RUN.txt`
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - the bundle reports zero parked and rejected totals and a soak failure set of `NONE`, while still preserving two kill signals and two unresolved promotion blockers
- intake handling:
  - keep the run as clean in parked/reject terms but not failure-free in lineage terms

## Tension 2: Same Filename Versus Different Packet Bytes
- source anchors:
  - detached top-level strategy packets
  - embedded `zip_packets/`
  - embedded `a1_inbox/consumed/`
- bounded contradiction:
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip` exists as two different byte payloads inside the same bundle depending on which surface is read
- intake handling:
  - preserve both variants explicitly; do not pick one as archive truth without external proof

## Tension 3: Working-Run Reproducibility Versus Missing Control Surfaces
- source anchors:
  - `README_WORKING_RUN.txt`
  - embedded run inventory
- bounded contradiction:
  - the README reads like a reproducible operator kit, but the bundle omits `sequence_state.json`, `HARDMODE_METRICS.json`, and the `sim/` subtree
- intake handling:
  - treat the bundle as a partial working-run capsule, not a self-contained replay package

## Tension 4: Event Proof Versus Missing Evidence Bodies
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the event and soak surfaces name runtime `sim/sim_evidence_*` paths, but no local evidence files are retained in the archive object
- intake handling:
  - retain the bundle as state-and-transport residue with incomplete evidence-body preservation

