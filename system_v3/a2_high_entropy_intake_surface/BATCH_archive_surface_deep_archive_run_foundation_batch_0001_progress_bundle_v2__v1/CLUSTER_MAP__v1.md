# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle_v2__v1`
Date: 2026-03-09

## Cluster 1: Patch-Lineage Export Kit
- archive meaning:
  - the bundle is not just a replay packet; it is an operator-facing patch assertion over an older foundation run
- bound evidence:
  - `README_PATCH_AND_RUN.txt` enumerates four runtime patch changes
  - the embedded run includes `sequence_state.json`, which matches the README emphasis on run-local resume
- retained interpretation:
  - this bundle should be read as a historical patched-export kit and not as active runtime truth

## Cluster 2: Hash-Bound Snapshot Integrity
- archive meaning:
  - the strongest preserved authority inside the bundle is state integrity, not semantic cleanliness
- bound evidence:
  - README final state hash, summary final state hash, `state.json` sha256, and `state.json.sha256` all converge on `84ce3614...`
  - `summary.json` and `soak_report.md` agree on a two-step `MAX_STEPS` terminal snapshot with `accepted_total 29`
- retained interpretation:
  - the bundle strongly preserves that a specific patched end state existed, but not that the surrounding run history is fully represented

## Cluster 3: Clean Continuation Versus Residual Failure Memory
- archive meaning:
  - the bundle preserves a split between a locally clean continuation and a globally dirty retained state
- bound evidence:
  - README says packet set `000010 + 000011` was accepted with no rejects or parks
  - summary and soak report say zero parked and rejected totals
  - `state.json` still carries `park_set_len 7`, `reject_log_len 11`, and `kill_log_len 7`
- retained interpretation:
  - the archive should preserve both claims at once: a clean local continuation happened, and prior failure texture remained part of the stored end state

## Cluster 4: Undercomplete Evidence Body
- archive meaning:
  - the bundle carries transport and hashes more faithfully than underlying evidence bodies
- bound evidence:
  - event rows and soak-report payloads reference runtime `sim/sim_evidence_*` paths
  - no `sim/` directory is retained inside the bundle
  - `sim_results` count `35` is preserved as state structure, not as bundled text outputs
- retained interpretation:
  - this is strong transport/state residue with weak evidence-body preservation

## Cluster 5: Packet Duplication And Ledger Narrowness
- archive meaning:
  - strategy packet carry is duplicated and wider than the embedded event ledger proves
- bound evidence:
  - top-level `packets/` contains `11` strategy zips
  - embedded `a1_inbox/consumed/` duplicates those same `11` zips byte-for-byte
  - `events.jsonl` references strategy packets only through `000009`
- retained interpretation:
  - the bundle over-preserves packet residue relative to the explicitly retained event proof

