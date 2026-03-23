# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001_progress_bundle__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_PROGRESS_BUNDLE_PASS`

## T1) README cumulative totals vs embedded final snapshot totals
- source markers:
  - `README_PROGRESS.txt`
  - `summary.json`
  - `soak_report.md`
- tension:
  - the README reports cumulative observed totals of `accepted 64`, `parked 7`, and `rejected 4`
  - the embedded summary and soak report collapse the retained run to `accepted_total 15`, `parked_total 0`, `rejected_total 0`, and `cycle_count 1`
- preserved read:
  - the bundle keeps both a cumulative replay narrative and a narrow final-snapshot view, and they are not interchangeable

## T2) Zeroed top-line park/reject counts vs retained state failure residue
- source markers:
  - `summary.json`
  - `state.json`
- tension:
  - top-line embedded surfaces say parked and rejected totals are zero
  - the state still retains `kill_log_len 5`, `park_set_len 7`, and `reject_log_len 11`
- preserved read:
  - the embedded snapshot summary hides failure texture that the state body still preserves

## T3) Seven carried strategy packets vs five referenced strategy events
- source markers:
  - `packets/`
  - `a1_inbox/consumed/`
  - `events.jsonl`
- tension:
  - the bundle carries `7` strategy zips in both external and consumed form
  - the embedded event ledger references only `000001`, `000002`, `000003`, `000005`, and `000007`, leaving `000004` and `000006` unreferenced
- preserved read:
  - the carried replay set is broader than the embedded event trace the bundle chose to preserve

## T4) Hash-stable embedded end state vs empty governing identifiers
- source markers:
  - `README_PROGRESS.txt`
  - `summary.json`
  - `state.json`
  - `state.json.sha256`
- tension:
  - the final state hash is repeated consistently across README, summary, state body, and sidecar
  - `active_megaboot_id`, `active_megaboot_sha256`, and `active_ruleset_sha256` remain empty strings
- preserved read:
  - the bundle preserves end-state integrity more strongly than governing-context identity

## T5) Replay/evidence path references vs missing retained sim evidence
- source markers:
  - `README_PROGRESS.txt`
  - `events.jsonl`
  - `soak_report.md`
  - embedded run inventory
- tension:
  - replay notes and event rows repeatedly reference runtime-path `sim/sim_evidence_*` files
  - the embedded run has no `sim/` directory at all
- preserved read:
  - the progress bundle keeps trace references to sim evidence without retaining the evidence bodies

## T6) Progress-bundle compression vs duplicate strategy carriage
- source markers:
  - bundle root inventory
  - `zip_packets/`
  - `packets/`
  - `a1_inbox/consumed/`
- tension:
  - the bundle omits heavier control surfaces such as `HARDMODE_METRICS.json` and `sequence_state.json`
  - it still duplicates the seven carried A1 strategy packets across two explicit side lanes
- preserved read:
  - compression in this bundle is selective: control summaries are dropped faster than packet replay material
