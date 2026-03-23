# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_det_a__v1`
Date: 2026-03-09

## Cluster 1: Two Executed Packet Cycles
- archive meaning:
  - the run preserves a compact but real two-step execution spine
- bound evidence:
  - events keep two `step_result` rows
  - packet lattice keeps two `A0_TO_B`, two `B_TO_A0`, and two `SIM_TO_A0` packets
  - soak and summary both total `accepted 7` and `rejected 1`
- retained interpretation:
  - useful historical small-run example where events, soak, and summary broadly agree on executed work

## Cluster 2: Queued Third A1 Continuation
- archive meaning:
  - the run does not stop at the end of the executed event spine; it also preserves a queued next strategy
- bound evidence:
  - `sequence_state.json` keeps `A1 3` while A0/B/SIM all stop at `2`
  - packet lattice includes `000003_A1_TO_A0_STRATEGY_ZIP.zip` without matching step-3 downstream packets
  - summary reports `steps_completed 3` and `3` unique strategy/export digests
- retained interpretation:
  - useful archive evidence of replay-authored continuation state surviving beyond executed transport

## Cluster 3: Replay-Only A1 Lineage
- archive meaning:
  - A1 strategy history survives only in transport packets, not in inbox residue
- bound evidence:
  - summary says `a1_source replay`
  - `a1_inbox/` is empty
  - all three A1 strategy packets live under `zip_packets/`
- retained interpretation:
  - useful lineage split between replay-authored strategy generation and normal inbox delivery

## Cluster 4: Summary Mostly Coherent But Not Fully Closed
- archive meaning:
  - this run is cleaner than several adjacent archive tests, but it still retains multi-surface closure gaps
- bound evidence:
  - summary, soak, and events agree on total accepted `7`, rejected `1`, and fail tag `SCHEMA_FAIL`
  - summary reports `3` completed steps while events and canonical ledger preserve only `2` executed steps
  - summary/state final hash is `3ce0407f...` while the last event hash ends on `232c1595...`
- retained interpretation:
  - useful archive object for partial coherence without total closure

## Cluster 5: Semantic Promotion Debt Without Packet Parks
- archive meaning:
  - packet counters stay clean while semantic promotion debt persists
- bound evidence:
  - summary and soak report `parked_total 0`
  - state keeps `3` `PARKED` sim promotion statuses and `3` unresolved promotion blockers
- retained interpretation:
  - useful historical example of semantic debt surviving clean packet transport

## Cluster 6: Operator Exhaustion Boundary
- archive meaning:
  - the stop condition is not generic truncation; it is explicit operator exhaustion under schema-fail pressure
- bound evidence:
  - summary stop reason is `A2_OPERATOR_SET_EXHAUSTED`
  - summary escalation reason is `OPERATOR_SET_EXHAUSTED:SCHEMA_FAIL`
  - state reject log preserves one `SCHEMA_FAIL`
- retained interpretation:
  - useful archive evidence of a bounded fail-closed ceiling rather than uncontrolled drift

## Cluster 7: Final Snapshot Anchors The Queued Packet
- archive meaning:
  - the queued third strategy packet is anchored to the final summary/state hash, not to the last executed event endpoint
- bound evidence:
  - `summary/state` final hash is `3ce0407f...`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip` uses `inputs.state_hash 3ce0407f...`
  - last executed event row ends on `232c1595...`
- retained interpretation:
  - useful archive evidence that the preserved continuation packet belongs to a later post-event snapshot layer
