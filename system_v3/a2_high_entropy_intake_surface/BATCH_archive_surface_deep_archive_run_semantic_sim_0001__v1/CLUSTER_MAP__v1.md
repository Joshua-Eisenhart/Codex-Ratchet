# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_semantic_sim_0001__v1`
Date: 2026-03-09

## Cluster 1: Coherent Five-Step Semantic-SIM Run
- archive meaning:
  - this object preserves a direct multi-step semantic-SIM run rather than the compressed step-one replay pattern seen in earlier archive runs
- bound evidence:
  - `summary.json` says `steps_completed 5`
  - `events.jsonl` preserves steps `1` through `5`
  - each step accepts `14` and emits `6` SIM outputs
- retained interpretation:
  - useful as a contrasting archive example where step counts and retained event rows actually align

## Cluster 2: Clean Transport With Heavy Promotion Debt
- archive meaning:
  - zero parked and zero rejected packet counters do not imply semantic closure
- bound evidence:
  - `summary.json` and `soak_report.md` both report `parked_total 0` and `rejected_total 0`
  - `state.json` keeps five pending canonical evidence items, ten kill signals, and thirty `PARKED` sim promotion states
  - promotion counts by tier are all failures and zero passes
- retained interpretation:
  - strong archive evidence that semantic promotion debt can scale independently of packet cleanliness

## Cluster 3: Root-Only Sequence Ledger
- archive meaning:
  - this run preserves only the global sequence ledger, not the inbox-local A1 ledger seen in some other run families
- bound evidence:
  - root `sequence_state.json` exists
  - `a1_inbox/sequence_state.json` is absent
  - `a1_inbox` contains only `consumed/`
- retained interpretation:
  - useful for lineage because it shows that inbox-local sequence retention is not stable across archive runs

## Cluster 4: Renumbered Consumed Strategy Lane
- archive meaning:
  - consumed strategy residue and embedded transport residue use different naming regimes
- bound evidence:
  - embedded strategy files are `000001` through `000005`
  - consumed strategy files are `400001` through `400005`
  - only `400001` is byte-identical to embedded `000001`
- retained interpretation:
  - useful demotion evidence because packet identity cannot be recovered from either naming scheme alone

## Cluster 5: Summary Fidelity Without Promotion Success
- archive meaning:
  - unlike earlier archive runs, the summary accurately reflects step count and digest diversity, but promotion truth still fails closed
- bound evidence:
  - summary unique digest counts are `5` and retained event digests are also `5`
  - summary accepted total `70` matches the five accepted-fourteen result rows
  - all thirty retained sim promotion states remain `PARKED`
- retained interpretation:
  - archive value here is not summary falseness but the gap between accurate accounting and absent promotion passes

## Cluster 6: Missing Local SIM Bodies Despite Runtime-Like Paths
- archive meaning:
  - the run preserves detailed runtime-like SIM evidence paths without retaining the local `sim/` directory
- bound evidence:
  - every retained SIM output points to a `sim/sim_evidence_*` path under runtime
  - no local `sim/` directory exists in the archived run root
- retained interpretation:
  - structurally rich archive object with missing evidence-body retention

