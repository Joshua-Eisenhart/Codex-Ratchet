# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_ladder_001__v1`
Date: 2026-03-09

## Tension 1: Clean Headline Versus Negative Kill Memory
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - the run reports zero parked and rejected totals and soak failure tags `NONE`, while state preserves one kill signal and summary preserves one unresolved promotion blocker
- intake handling:
  - keep the run as clean in parked/reject terms without erasing the remaining negative seam

## Tension 2: Semantic Action Name Versus Protocol Packet Name
- source anchors:
  - `a1_inbox/consumed/000001_FND_LR_ACTION.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - the same bytes are preserved under a semantic action label on the consumed surface and a generic protocol transport label on the packet surface
- intake handling:
  - preserve both names explicitly as historical lineage rather than choosing one as authoritative

## Tension 3: Direct Run Integrity Versus Missing Local Evidence Bodies
- source anchors:
  - `state.json`
  - `state.json.sha256`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the run is hash-consistent and structurally intact, but it still references local sim evidence paths that are not retained in the archive object
- intake handling:
  - treat the run as a valid state/transport artifact with incomplete evidence-body preservation

