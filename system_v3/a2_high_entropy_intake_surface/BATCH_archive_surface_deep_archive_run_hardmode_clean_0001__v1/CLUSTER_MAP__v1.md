# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_hardmode_clean_0001__v1`
Date: 2026-03-09

## Cluster 1: Large Hardmode-Clean Run Capsule
- archive meaning:
  - this object preserves a large-scale direct run whose top-line metrics are deliberately clean on park/reject counts
- bound evidence:
  - `summary.json` shows `accepted_total 1400`, `parked_total 0`, `rejected_total 0`
  - `soak_report.md` shows `cycle_count 100` and top failure tags `NONE`
  - `HARDMODE_METRICS.json` is retained at the run root
- retained interpretation:
  - useful historical example of a run that brands itself as clean while still carrying large lower-level burdens

## Cluster 2: Pending And Kill Burden Under A Clean Window
- archive meaning:
  - the run is clean only at the packet rejection layer, not at the semantic burden layer
- bound evidence:
  - `kill_log_len 440`
  - `evidence_pending_len 220`
  - `unresolved_promotion_blocker_count 440`
  - hardmode metrics include `PARKED 440` promotion statuses
- retained interpretation:
  - the archive preserves a clear demotion pattern: clean transport totals can coexist with massive unresolved semantic load

## Cluster 3: Event/Step Counting Split
- archive meaning:
  - the run stores at least two counting regimes simultaneously
- bound evidence:
  - summary/soak report say `100` steps/cycles
  - event ledger contains `220` step-result rows
  - event step field reaches `120` and repeats across the first `100` step values
- retained interpretation:
  - historical consumers should not collapse summary step counts and event step fields into one metric

## Cluster 4: Divergent Strategy-Packet Lanes
- archive meaning:
  - consumed strategy residue and embedded transport strategy packets are related but not interchangeable
- bound evidence:
  - both lanes have `220` packets
  - filenames are offset `400001`-`400220` versus `000001`-`000220`
  - only one aligned pair matches byte-for-byte; the other `219` differ
- retained interpretation:
  - this run is strong evidence that consumed input lanes and embedded transport lanes cannot be treated as one authority surface by default

## Cluster 5: Evidence Bodies Missing At Scale
- archive meaning:
  - the run keeps massive packet/state residue but omits the local sim evidence texts it cites
- bound evidence:
  - `1320` SIM result packets are referenced and retained
  - event and soak rows repeatedly cite runtime `sim/sim_evidence_*` paths
  - no `sim/` directory is present in the archive object
- retained interpretation:
  - the archive is better for structural lineage and burden mapping than for reconstructing full evidence content

