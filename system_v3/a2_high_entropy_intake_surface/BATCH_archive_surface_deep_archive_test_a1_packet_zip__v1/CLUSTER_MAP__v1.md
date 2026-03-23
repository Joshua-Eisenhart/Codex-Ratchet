# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
Date: 2026-03-09

## Cluster 1: Single-Step Packet Loop With All Four Active Lanes
- archive meaning:
  - this run preserves the smallest visible closed transport loop rather than an A0-only stub
- bound evidence:
  - `zip_packets/` contains one `A1_TO_A0`, one `A0_TO_B`, one `B_TO_A0`, and one `SIM_TO_A0` packet
  - all packet headers use sequence `1`
- retained interpretation:
  - useful historical boundary object for packet-loop structure at minimum scale

## Cluster 2: Summary Collapse Versus Richer State Residue
- archive meaning:
  - top-line summary understates what the deeper state and event surfaces retain
- bound evidence:
  - summary reports `accepted_total 0` and zero unique digests
  - state keeps `accepted_batch_count 2`, a two-entry canonical ledger, two evidence tokens, two kill signals, one schema-fail reject, and three parked sim promotion states
- retained interpretation:
  - useful archive evidence that the terminal summary cannot be treated as a complete account

## Cluster 3: Zeroed Global Sequence Ledger
- archive meaning:
  - the explicit sequence surface has been flattened despite visible packet presence
- bound evidence:
  - `sequence_state.json` reports `A0 0`, `A1 0`, `B 0`, and `SIM 0`
  - the run root still carries one packet in each active lane
- retained interpretation:
  - useful contradiction for demotion lineage around sequence tracking

## Cluster 4: Duplicated Success And Failure Event Rows
- archive meaning:
  - the event ledger is not a clean one-row step trace
- bound evidence:
  - `events.jsonl` contains `32` rows
  - `3` identical success rows all report step `1`, accepted `2`, and the same digests
  - `29` identical `a1_generation_fail` rows repeat one schema-fail error
- retained interpretation:
  - useful archive evidence of ledger inflation at a single step

## Cluster 5: Split Strategy Packet Family By Location
- archive meaning:
  - same-name strategy packets do not preserve one canonical payload across locations
- bound evidence:
  - inbox and consumed copies are byte-identical to each other and schema-invalid
  - transport-lane copy differs in size, hash, and payload richness
- retained interpretation:
  - useful demotion example where packet path matters more than filename identity

## Cluster 6: One Accepted Export/Snapshot/SIM Spine
- archive meaning:
  - beneath the duplicated ledger noise, the packet lattice still preserves a coherent accepted spine
- bound evidence:
  - export block proposes `P_BIND_ALPHA` and `S_BIND_ALPHA_S0001`
  - Thread-S snapshot records `ACCEPTED_BATCH_COUNT=1`
  - SIM evidence preserves one perturbation result for `S_BIND_ALPHA_S0001`
- retained interpretation:
  - useful historical trace of one accepted baseline path before fail-closed regeneration noise dominates

## Cluster 7: Schema-Failed Regeneration Overlay
- archive meaning:
  - the run also preserves a later fail-closed regeneration lane against the same step
- bound evidence:
  - repeated fail rows cite `alternatives must be non-empty` and `candidate_count must equal len(targets)`
  - inbox/consumed strategy packet copies match that invalid shape with zero alternatives and zero candidates
  - state reject log records `SCHEMA_FAIL`
- retained interpretation:
  - useful archive evidence that invalid regeneration can coexist with earlier accepted packet artifacts

## Cluster 8: Final Hash Drift Across Surfaces
- archive meaning:
  - integrity still does not collapse across summary, state evolution, and event endpoint
- bound evidence:
  - summary/state sidecar align on final hash `aed8327f...`
  - duplicated success rows end on `state_hash_after 3aede158...`
  - transport-lane strategy packet points back to prior state hash `de0e5fe9...`
- retained interpretation:
  - useful historical example of multi-surface state divergence inside a tiny packet run
