# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_PROGRESS_BUNDLE_PASS`

## C1) Replay README surface
- members:
  - `README_PROGRESS.txt`
- retained read:
  - the bundle is explicitly an operator-facing replay kit with a staged injection script and deterministic issue notes

## C2) Embedded final snapshot surface
- members:
  - `RUN_FOUNDATION_BATCH_0001/summary.json`
  - `RUN_FOUNDATION_BATCH_0001/state.json`
  - `RUN_FOUNDATION_BATCH_0001/state.json.sha256`
  - `RUN_FOUNDATION_BATCH_0001/soak_report.md`
- retained read:
  - the embedded run snapshot is one-step and hash-stable, but it still carries kill, park, and reject residue inside the state body

## C3) Compact event-ledger surface
- members:
  - `RUN_FOUNDATION_BATCH_0001/events.jsonl`
- retained read:
  - the event stream is a short replay trace, not a long campaign ledger

## C4) Embedded mixed packet subset surface
- members:
  - `RUN_FOUNDATION_BATCH_0001/zip_packets/*`
- retained read:
  - the embedded run carries a small mixed packet lattice containing one save point, five export/update pairs, seven strategies, and twenty-five sim results

## C5) Duplicated carried strategy surface
- members:
  - `packets/*`
  - `RUN_FOUNDATION_BATCH_0001/a1_inbox/consumed/*`
- retained read:
  - the carried strategy set is duplicated byte-for-byte in two places outside and inside the embedded run

## C6) Missing-control surface
- members:
  - absent `HARDMODE_METRICS.json`
  - absent `sequence_state.json`
  - absent `sim/`
- retained read:
  - the bundle compresses replay progress much more aggressively than the full run capsule shape

## C7) Deferred next family
- next bounded target:
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE_v2`
- reason:
  - it is the immediate sibling revision of this replay/export family and should expose what changed between the first and second progress surfaces
