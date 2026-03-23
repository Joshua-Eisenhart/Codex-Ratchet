# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_bundle__v1`
Date: 2026-03-09

## Cluster 1: Operator Recipe Capsule
- archive meaning:
  - this bundle is a working-run operator capsule rather than a generalized replay export
- bound evidence:
  - `README_WORKING_RUN.txt` preserves explicit commands and expected summary metrics
  - the bundle root carries only the two detached strategy packets needed for the continuation
- retained interpretation:
  - its archive value is procedural reproducibility at small scale, not completeness

## Cluster 2: Clean Compact Final Snapshot
- archive meaning:
  - the embedded child run is a very small, clean-looking two-step snapshot
- bound evidence:
  - `summary.json` reports `accepted_total 30`, `parked_total 0`, `rejected_total 0`
  - `state.json` also shows `park_set_len 0` and `reject_log_len 0`
  - all hash anchors converge on `e2037bac...`
- retained interpretation:
  - the bundle preserves a genuine clean-state capsule, unlike later archive derivatives that keep heavier parked/reject residue

## Cluster 3: Hidden Failure Signal Residue
- archive meaning:
  - even this clean capsule retains a narrow negative lineage under the headline
- bound evidence:
  - `kill_log_len 2`
  - `unresolved_promotion_blocker_count 2`
  - both kill-log entries use `NEG_NEG_COMMUTATIVE_ASSUMPTION`
  - `soak_report.md` still says top failure tags `NONE`
- retained interpretation:
  - negative SIM outcomes survive as kill-signal memory even when the bundle frames itself as clean

## Cluster 4: Incomplete Evidence Body
- archive meaning:
  - the bundle preserves event and packet residue more strongly than evidence bodies
- bound evidence:
  - `events.jsonl` and `soak_report.md` reference runtime `sim/sim_evidence_*` paths
  - no `sim/` directory is retained inside the bundle
  - no `sequence_state.json` is retained even though the run spans two steps
- retained interpretation:
  - the bundle is a compact historical capsule, not a full self-sufficient replay artifact

## Cluster 5: Same-Name Packet Divergence
- archive meaning:
  - the bundle keeps two different byte payloads under the same strategy-packet filename family
- bound evidence:
  - top-level `000002_A1_TO_A0_STRATEGY_ZIP.zip` is `833b223e...`
  - embedded `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip` is `573d01fa...`
  - `a1_inbox/consumed/000002_A1_TO_A0_STRATEGY_ZIP.zip` matches the detached top-level packet, not the embedded `zip_packets` copy
- retained interpretation:
  - the bundle preserves unresolved internal packet lineage and should not be flattened into one authoritative `000002` strategy packet

