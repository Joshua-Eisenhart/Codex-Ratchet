# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005__v1`
Date: 2026-03-09

## Cluster 1: Fully Aligned Sixty-Pass Signal Run
- archive meaning:
  - this object preserves the repaired version of the signal-plus-audit family where summary, state, sequence, soak, and event counts all align
- bound evidence:
  - `summary.json` says `steps_completed 60` and `accepted_total 960`
  - `events.jsonl` keeps exactly `60` result rows over steps `1` through `60`
  - `state.json` keeps `accepted_batch_count 60`
  - `sequence_state.json` ends with `A1 60`
- retained interpretation:
  - useful as an archive contrast to `RUN_SIGNAL_0004`, where the compression bug was still present

## Cluster 2: Clean Transport With Heavy Promotion Debt
- archive meaning:
  - zero parked and zero rejected packet counters do not imply semantic closure
- bound evidence:
  - `summary.json` and `soak_report.md` both report `parked_total 0` and `rejected_total 0`
  - `state.json` keeps `60` pending canonical evidence items, `240` kill signals, and `360` `PARKED` sim promotion states
  - promotion counts by tier are all failures and zero passes
- retained interpretation:
  - strong archive evidence that semantic promotion debt remains even after summary/event alignment is repaired

## Cluster 3: Dual Audit Overlay Still Persists
- archive meaning:
  - this run still carries two historical audit surfaces in addition to the runtime-like run artifacts
- bound evidence:
  - `SIGNAL_AUDIT.json` is a compact structural readout that now aligns with the sixty-pass runtime surface
  - `REPLAY_AUDIT.json` reconstructs all `541` packet events and marks determinism `pass true`
- retained interpretation:
  - valuable archive layer because post-run interpretive overlays remain part of the history even after the runtime-facing counts are repaired

## Cluster 4: Deterministic Replay With Divergent Final Hash
- archive meaning:
  - replay determinism still does not collapse replay truth into run-final truth
- bound evidence:
  - `REPLAY_AUDIT.json` shows matching first/second trace hashes and emitted artifact hashes
  - replay final hash is `ed1a34...`
  - summary/state final hash is `0045ff...`
  - last retained event row ends at `299c9c...`
- retained interpretation:
  - useful historical example where runtime-facing counts are repaired but closure still splits across three nonidentical hash surfaces

## Cluster 5: Renumbered And Divergent Consumed Strategy Lane
- archive meaning:
  - consumed strategy residue and embedded transport residue use different naming regimes and almost entirely different bytes
- bound evidence:
  - embedded strategy files are `000001` through `000060`
  - consumed strategy files are `400001` through `400060`
  - only step `1` is byte-identical across the two lanes
- retained interpretation:
  - useful demotion evidence because packet identity cannot be reconstructed from filename order alone

## Cluster 6: Replay Parks Most of the Packet Corpus
- archive meaning:
  - reconstructive replay treats most retained packets as park outcomes rather than a clean replayed execution
- bound evidence:
  - `REPLAY_AUDIT.json` keeps `541` replay events
  - only `60` are `OK`
  - `481` are `PARK`
  - replay reasons are limited to `REPLAY_PREREQ_MISSING_FORWARD`, `MISSING_FORWARD_SEQUENCE:A0:1`, and `SEQUENCE_GAP`
- retained interpretation:
  - archive value here is not replay success but replay failure texture under deterministic audit conditions

## Cluster 7: Signal Audit Null Field Amid Nonzero Kill Metadata
- archive meaning:
  - the compact audit surface is cleaner than `RUN_SIGNAL_0004` on step alignment, but it still carries an unresolved nullability seam
- bound evidence:
  - `SIGNAL_AUDIT.json` says `kill_kind_counts.MATH_DEF 120`
  - the same file sets `killed_math_count` to `null`
- retained interpretation:
  - useful archive evidence that even the repaired audit layer is not semantically closed

## Cluster 8: Missing Local SIM Bodies Despite Runtime-Like Paths
- archive meaning:
  - the run preserves detailed runtime-like SIM evidence paths without retaining the local `sim/` directory
- bound evidence:
  - event and soak surfaces reference concrete `sim/sim_evidence_*` runtime paths
  - no local `sim/` directory exists in the archived run root
  - `zip_packets/` still retains all `360` `SIM_TO_A0_SIM_RESULT_ZIP` files
- retained interpretation:
  - structurally rich archive object with strong packet evidence and weak retained evidence-body locality
