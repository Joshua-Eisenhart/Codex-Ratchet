# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_registry_smoke_0001__v1`
Date: 2026-03-09

## Cluster 1: Minimal Queue-Drained Smoke Run
- archive meaning:
  - this object preserves a very small direct smoke run after two strategy packets were consumed, not a live-backlog snapshot and not a wrapper bundle
- bound evidence:
  - `a1_inbox/consumed/` contains two strategy packets
  - no live strategy packet files remain in `a1_inbox/`
  - no wrapper README or `HARDMODE_METRICS.json` is present
- retained interpretation:
  - useful as the smallest transport-clean historical example in this archive family

## Cluster 2: Headline Compression Over Two Accepted Passes
- archive meaning:
  - the run surface collapses two accepted result passes into one nominal completed step and one accepted-total window
- bound evidence:
  - `summary.json` says `steps_completed 1` and `accepted_total 7`
  - `events.jsonl` keeps two accepted result rows
  - both retained result rows show `accepted 7`
- retained interpretation:
  - this archive object should be read as a compressed two-pass smoke run, not as a literal single accepted pass

## Cluster 3: Clean Packet Counters With Parked Semantic Debt
- archive meaning:
  - packet-level cleanliness does not imply semantic promotion closure
- bound evidence:
  - `summary.json` and `soak_report.md` both report zero parked and zero rejected
  - `state.json` keeps two pending evidence items, four kill signals, and four `PARKED` sim promotion states
- retained interpretation:
  - useful archive evidence that demotion burden can persist even when transport counters remain clean

## Cluster 4: Digest Collapse At Summary Level
- archive meaning:
  - the final summary erases some retained digest diversity even in this minimal run
- bound evidence:
  - `summary.json` sets each unique digest family count to `1`
  - retained result rows preserve `2` strategy digests, `2` export content digests, and `2` export structural digests
- retained interpretation:
  - high-value contradiction because the same compression pattern appears even at smoke-run scale

## Cluster 5: Empty-Path SIM References
- archive meaning:
  - the run preserves SIM-result references without any retained evidence-body location
- bound evidence:
  - all retained `sim_outputs[].path` fields are empty strings
  - no local `sim/` directory exists in the archived run root
- retained interpretation:
  - this is a stronger evidence-body absence signal than the larger runs, which at least kept runtime-like path strings

## Cluster 6: Same-Name Strategy Divergence
- archive meaning:
  - consumed input residue and embedded transport residue are unstable by filename identity even in the smallest two-packet family
- bound evidence:
  - consumed and embedded lanes both preserve `000001` and `000002`
  - both pairwise hash comparisons are mismatches
- retained interpretation:
  - compact but strong packet-lineage demotion evidence

