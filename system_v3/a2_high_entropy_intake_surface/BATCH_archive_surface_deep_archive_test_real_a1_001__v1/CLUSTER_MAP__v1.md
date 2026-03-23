# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
Date: 2026-03-09

## Cluster 1: One-Step Clean Packet Spine
- archive meaning:
  - this run preserves a compact one-step execution without queued continuation residue
- bound evidence:
  - one `step_result` row in events
  - one `A1_TO_A0` strategy packet, one `A0_TO_B` export packet, one `B_TO_A0` snapshot packet, and two `SIM_TO_A0` packets
  - summary and soak both report `accepted 4`, `rejected 0`, and `MAX_STEPS`
- retained interpretation:
  - useful historical example of a small, transport-clean, one-step run

## Cluster 2: Real-A1-Named Run With Replay Attribution
- archive meaning:
  - the run name suggests real-A1 lineage while the retained metadata attributes the strategy source to replay
- bound evidence:
  - run id is `TEST_REAL_A1_001`
  - summary says `a1_source replay`
  - `needs_real_llm false`
  - inbox is empty
- retained interpretation:
  - useful naming-versus-lineage contradiction for archive history

## Cluster 3: Dual-SIM Evidence Without Second-Step Transport
- archive meaning:
  - the single step fans out into two retained SIM evidence returns rather than a queued second strategy
- bound evidence:
  - one target spec and one alternative spec are present in the strategy packet
  - two SIM result packets survive with distinct `SIM_ID`s
  - no retained second strategy, export, or snapshot packet exists
- retained interpretation:
  - useful archive example of one-step branching resolved inside the SIM layer rather than through later strategy progression

## Cluster 4: Final Snapshot Above Event Endpoint
- archive meaning:
  - final closure still does not collapse to the only executed event row
- bound evidence:
  - summary/state sidecar bind to `d0f83cb5...`
  - the sole event row ends on `6835e766...`
  - no retained sequence ledger explains the transition between them
- retained interpretation:
  - useful archive evidence of post-event snapshot drift even in a small clean run

## Cluster 5: Semantic Promotion Debt Without Packet Parks
- archive meaning:
  - packet counters stay clean while semantic promotion closure remains open
- bound evidence:
  - summary and soak report `parked_total 0`
  - state keeps `2` `PARKED` sim promotion states and `2` unresolved blockers
- retained interpretation:
  - useful historical example of unresolved promotion debt surviving clean transport

## Cluster 6: Snapshot Pending Evidence Versus Empty `evidence_pending`
- archive meaning:
  - the human-readable snapshot and machine state disagree on where pending evidence is recorded
- bound evidence:
  - `THREAD_S_SAVE_SNAPSHOT_v2.txt` lists pending evidence for both retained specs
  - `state.json` keeps `evidence_pending` empty
- retained interpretation:
  - useful archive seam between snapshot text and final machine-state normalization

## Cluster 7: SIM Kill Signals Versus Empty State Kill Log
- archive meaning:
  - kill-signal residue survives at the SIM packet layer but not in final state bookkeeping
- bound evidence:
  - both SIM evidence files emit `KILL_SIGNAL ... NEG_NEG_BOUNDARY`
  - `state.json` keeps `kill_log` empty
- retained interpretation:
  - useful archive example of packet-body evidence outrunning final state aggregation
