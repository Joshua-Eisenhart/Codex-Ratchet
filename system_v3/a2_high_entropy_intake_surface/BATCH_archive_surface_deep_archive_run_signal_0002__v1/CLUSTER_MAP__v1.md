# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0002__v1`
Date: 2026-03-09

## Cluster 1: Fifty-Step Signal Run With Stable Per-Step Shape
- archive meaning:
  - this object preserves a direct long-run signal family rather than a compressed replay or queue-collapse artifact
- bound evidence:
  - `summary.json` says `steps_completed 50`
  - `events.jsonl` preserves steps `1` through `50`
  - each step accepts `14` and emits `6` SIM outputs
- retained interpretation:
  - useful as a large-scale archive example where step count, accepted count, and digest diversity all stay internally consistent

## Cluster 2: Clean Transport With Massive Promotion Debt
- archive meaning:
  - zero parked and zero rejected packet counters do not imply semantic closure, even in a stable long run
- bound evidence:
  - `summary.json` and `soak_report.md` both report `parked_total 0` and `rejected_total 0`
  - `state.json` keeps fifty pending canonical evidence items, one hundred kill signals, and three hundred `PARKED` sim promotion states
  - promotion counts by tier are all failures and zero passes
- retained interpretation:
  - strong archive evidence that semantic promotion debt scales independently of clean packet transport

## Cluster 3: Accurate Summary Counters With Event-Endpoint Hash Drift
- archive meaning:
  - the summary is mostly faithful on step and digest totals, but the retained event lattice does not itself end on the final state hash
- bound evidence:
  - summary accepted total `700` matches fifty accepted-fourteen result rows
  - summary unique digest counts are `50`, and retained event digests are also `50`
  - last event `state_hash_after` is `496d...`, while final `summary/state` hash is `3d77...`
- retained interpretation:
  - useful as a historical example where accounting fidelity is high but event-ledger closure is weaker than final snapshot integrity

## Cluster 4: Root-Only Sequence Ledger
- archive meaning:
  - this run preserves only the global sequence ledger, not the inbox-local A1 ledger
- bound evidence:
  - root `sequence_state.json` exists with `A1 50`
  - `a1_inbox/sequence_state.json` is absent
  - `a1_inbox` contains only `consumed/`
- retained interpretation:
  - useful for lineage because inbox-local sequence retention is still not stable even in a larger cleaner run family

## Cluster 5: Renumbered And Divergent Consumed Strategy Lane
- archive meaning:
  - consumed strategy residue and embedded transport residue use different naming regimes and mostly different bytes
- bound evidence:
  - embedded strategy files are `000001` through `000050`
  - consumed strategy files are `400001` through `400050`
  - only step `1` is byte-identical across the two lanes
- retained interpretation:
  - useful demotion evidence because packet identity cannot be reconstructed from filename order alone

## Cluster 6: Missing Local SIM Bodies Despite Runtime-Like Paths
- archive meaning:
  - the run preserves detailed runtime-like SIM evidence paths without retaining the local `sim/` directory
- bound evidence:
  - every retained result row carries `sim/sim_evidence_*` paths under runtime
  - no local `sim/` directory exists in the archived run root
  - `zip_packets/` still retains all `300` `SIM_TO_A0_SIM_RESULT_ZIP` files
- retained interpretation:
  - structurally rich archive object with strong packet evidence and weak retained evidence-body locality
