# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
Date: 2026-03-09

## Cluster 1: Two Executed Transitions Plus One Queued Third Strategy
- archive meaning:
  - this run preserves two completed state transitions and one queued continuation proposal
- bound evidence:
  - `state.json` keeps `accepted_batch_count 2` and canonical ledger length `2`
  - `events.jsonl` preserves only step `1` and step `2`
  - `sequence_state.json` keeps `A1 3`
  - `zip_packets/` contains `000003_A1_TO_A0_STRATEGY_ZIP.zip` with no matching third-step export, snapshot, or SIM packet
- retained interpretation:
  - useful historical example of a run root that keeps queued continuation residue above the executed state spine

## Cluster 2: Replay Attribution With Real-LLM Demand Flag
- archive meaning:
  - the run is replay-attributed, but the retained summary still marks `needs_real_llm true`
- bound evidence:
  - summary says `a1_source replay`
  - summary says `needs_real_llm true`
- retained interpretation:
  - useful archive contradiction for lineage classification; replay sourcing does not imply self-sufficiency

## Cluster 3: Summary And Soak Count Three Cycles While Executed Ledger Counts Two
- archive meaning:
  - top-line counters include the queued third strategy while the executed event/state surfaces stop at two transitions
- bound evidence:
  - summary says `steps_completed 3`
  - soak says `cycle_count 3`
  - sequence counters say `A1 3`
  - canonical ledger and events both stop at `2`
- retained interpretation:
  - useful historical seam between queued strategy generation and executed lower-loop completion

## Cluster 4: Final Hash Feeds The Queued Third Strategy
- archive meaning:
  - the queued third strategy is rooted on the retained final state rather than on a new executed event endpoint
- bound evidence:
  - summary/state sidecar bind to `3ce0407f...`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip` uses `inputs.state_hash 3ce0407f...`
  - last executed event ends on `232c1595...`
- retained interpretation:
  - useful archive example of queued continuation being minted from a final snapshot not explained by the visible event lattice

## Cluster 5: Second-Step Downshift With Mixed Survivor Carryover
- archive meaning:
  - step `2` downshifts from `PERTURBATION/T1_COMPOUND` to `BASELINE/T0_ATOM`, but final survivor state advances only the alternative lane
- bound evidence:
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip` proposes `S_BIND_ALPHA_S0002` and `S_BIND_ALPHA_ALT_ALT_S0002`
  - second snapshot and final state keep `S_BIND_ALPHA_ALT_ALT_S0002` but retain `S_BIND_ALPHA_S0001`
  - step `2` also records `SCHEMA_FAIL`
- retained interpretation:
  - useful archive seam where target lineage stalls while the alternative lane advances

## Cluster 6: Mixed-Suffix Duplicate File Family
- archive meaning:
  - the run root includes a second top-level file family that is byte-identical to the primary surfaces, but the suffix numbers are not uniform
- bound evidence:
  - `summary 3.json`, `state 2.json`, `state.json 2.sha256`, `events 2.jsonl`, `sequence_state 3.json`, and `soak_report 3.md` all hash-match the primary files
- retained interpretation:
  - useful packaging-residue example that must not be mistaken for a distinct runtime branch

## Cluster 7: Event Schema, Path Drift, And Empty Packet Shell
- archive meaning:
  - the retained executed ledger uses a variant step-result shape, still points to live-runtime packet paths, and the root keeps an extra empty `zip_packets 2/` shell
- bound evidence:
  - `events.jsonl` rows have no explicit `event` key
  - counters use `accepted` / `rejected` rather than `accepted_count` / `rejected_count`
  - export/strategy/sim packet paths point under `system_v3/runtime/...`
  - `sim_outputs[].path` is empty while `sim_outputs[].zip` is populated
  - `zip_packets 2/` exists and is empty
- retained interpretation:
  - useful archive seam between runtime-emitted event schema, later archive relocation, and packaging residue
