# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0003__v1`
Date: 2026-03-09

## Cluster 1: Thirty-Step Signal Run With Stable Per-Step Shape
- archive meaning:
  - this object preserves a direct mid-scale signal family rather than a compressed replay or queue-collapse artifact
- bound evidence:
  - `summary.json` says `steps_completed 30`
  - `events.jsonl` preserves steps `1` through `30`
  - each step accepts `16` and emits `6` SIM outputs
- retained interpretation:
  - useful as a contrast run where a smaller step count still increases per-step accepted yield relative to `RUN_SIGNAL_0002`

## Cluster 2: Clean Transport With Heavy Promotion Debt
- archive meaning:
  - zero parked and zero rejected packet counters do not imply semantic closure
- bound evidence:
  - `summary.json` and `soak_report.md` both report `parked_total 0` and `rejected_total 0`
  - `state.json` keeps thirty pending canonical evidence items, one hundred twenty kill signals, and one hundred eighty `PARKED` sim promotion states
  - promotion counts by tier are all failures and zero passes
- retained interpretation:
  - strong archive evidence that semantic promotion debt persists even when packet transport remains clean

## Cluster 3: Accurate Summary Counters With Event-Endpoint Hash Drift
- archive meaning:
  - the summary is faithful on step and digest totals, but the retained event lattice does not itself end on the final state hash
- bound evidence:
  - summary accepted total `480` matches thirty accepted-sixteen result rows
  - summary unique digest counts are `30`, and retained event digests are also `30`
  - last event `state_hash_after` is `1aad...`, while final `summary/state` hash is `d4b5...`
- retained interpretation:
  - useful as a historical example where accounting fidelity is high but event-ledger closure is weaker than final snapshot integrity

## Cluster 4: Root-Only Sequence Ledger
- archive meaning:
  - this run preserves only the global sequence ledger, not the inbox-local A1 ledger
- bound evidence:
  - root `sequence_state.json` exists with `A1 30`
  - `a1_inbox/sequence_state.json` is absent
  - `a1_inbox` contains only `consumed/`
- retained interpretation:
  - useful for lineage because inbox-local sequence retention still fails to persist across this signal family

## Cluster 5: Renumbered And Divergent Consumed Strategy Lane
- archive meaning:
  - consumed strategy residue and embedded transport residue use different naming regimes and mostly different bytes
- bound evidence:
  - embedded strategy files are `000001` through `000030`
  - consumed strategy files are `400001` through `400030`
  - only step `1` is byte-identical across the two lanes
- retained interpretation:
  - useful demotion evidence because packet identity cannot be reconstructed from filename order alone

## Cluster 6: Doubled Negative Kill Retention
- archive meaning:
  - the negative semantic residue is not just SIM-level; it duplicates into paired math-alternative ids
- bound evidence:
  - `kill_log_len` is `120` across `30` steps
  - each negative token appears `60` times
  - samples pair `S_SIM_NEG_A_*` with `S_MATH_ALT_A_*` and `S_SIM_NEG_B_*` with `S_MATH_ALT_B_*`
- retained interpretation:
  - useful archive evidence of semantic residue inflation without any corresponding packet-level park/reject growth

## Cluster 7: Missing Local SIM Bodies Despite Runtime-Like Paths
- archive meaning:
  - the run preserves detailed runtime-like SIM evidence paths without retaining the local `sim/` directory
- bound evidence:
  - every retained result row carries `sim/sim_evidence_*` paths under runtime
  - no local `sim/` directory exists in the archived run root
  - `zip_packets/` still retains all `180` `SIM_TO_A0_SIM_RESULT_ZIP` files
- retained interpretation:
  - structurally rich archive object with strong packet evidence and weak retained evidence-body locality
