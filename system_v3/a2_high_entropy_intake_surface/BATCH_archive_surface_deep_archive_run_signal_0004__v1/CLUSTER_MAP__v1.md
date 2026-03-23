# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0004__v1`
Date: 2026-03-09

## Cluster 1: Compressed Forty-Step Summary Over Sixty Retained Strategy Passes
- archive meaning:
  - this object preserves a compressed signal run whose visible step narrative is smaller than its retained packet and state lattice
- bound evidence:
  - `summary.json` says `steps_completed 40`
  - `events.jsonl` keeps `60` result rows with visible steps only `1` through `40`
  - steps `1` through `20` are duplicated, producing `60` strategy digests and `60` export digests
  - `state.json` and `sequence_state.json` both preserve `A1 60` / `accepted_batch_count 60`
- retained interpretation:
  - useful archive evidence of summary compression over a larger retained transport surface

## Cluster 2: Clean Transport With Massive Promotion Debt
- archive meaning:
  - zero parked and zero rejected packet counters do not imply semantic closure
- bound evidence:
  - `summary.json` and `soak_report.md` both report `parked_total 0` and `rejected_total 0`
  - `state.json` keeps `60` pending canonical evidence items, `240` kill signals, and `360` `PARKED` sim promotion states
  - promotion counts by tier are all failures and zero passes
- retained interpretation:
  - strong archive evidence that semantic promotion debt scales harder than the compressed summary implies

## Cluster 3: Dual Audit Overlay
- archive meaning:
  - this run carries two historical audit surfaces in addition to the runtime-like run artifacts
- bound evidence:
  - `SIGNAL_AUDIT.json` is a compact structural readout mixing `40` completed steps with `60` canonical items and `360` SIM items
  - `REPLAY_AUDIT.json` reconstructs all `541` packet events and marks determinism `pass true`
- retained interpretation:
  - valuable archive layer because it shows post-run interpretive overlays rather than just raw retained state

## Cluster 4: Deterministic Replay With Divergent Final Hash
- archive meaning:
  - replay determinism does not collapse replay truth into run-final truth
- bound evidence:
  - `REPLAY_AUDIT.json` shows matching first/second trace hashes and emitted artifact hashes
  - replay final hash is `e840db...`
  - summary/state final hash is `6e07a4...`
  - last retained event row ends at `d08f6d...`
- retained interpretation:
  - useful historical example where three different closure surfaces coexist without being smoothed into one authority

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

## Cluster 7: Missing Local SIM Bodies Despite Runtime-Like Paths
- archive meaning:
  - the run preserves detailed runtime-like SIM evidence paths without retaining the local `sim/` directory
- bound evidence:
  - event and soak surfaces reference concrete `sim/sim_evidence_*` runtime paths
  - no local `sim/` directory exists in the archived run root
  - `zip_packets/` still retains all `360` `SIM_TO_A0_SIM_RESULT_ZIP` files
- retained interpretation:
  - structurally rich archive object with strong packet evidence and weak retained evidence-body locality
