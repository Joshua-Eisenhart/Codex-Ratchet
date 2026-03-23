# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0004__v1`
Date: 2026-03-09

## Cluster 1: Queue-Drained Eight-Pass Autoratchet Run
- archive meaning:
  - this object preserves a direct QIT autoratchet run after eight strategy packets were consumed, not a live-backlog snapshot and not a wrapper bundle
- bound evidence:
  - `a1_inbox/consumed/` contains eight strategy packets
  - no live strategy packet files remain in `a1_inbox/`
  - no wrapper README or `HARDMODE_METRICS.json` is present
- retained interpretation:
  - useful as a historical example of a drained-but-still-unresolved autoratchet run at a larger packet scale

## Cluster 2: Step Compression Over Eight Retained Result Passes
- archive meaning:
  - the run surface collapses eight retained result passes into one nominal completed step
- bound evidence:
  - `summary.json` says `steps_completed 1`
  - `events.jsonl` keeps one explicit request row plus eight retained result rows
  - every retained result row still uses step value `1`
- retained interpretation:
  - this archive object should be read as repeated step-one replay compressed into one headline step

## Cluster 3: Digest Collapse At Summary Level
- archive meaning:
  - the final summary erases most of the retained digest diversity that the result rows still preserve
- bound evidence:
  - `summary.json` sets `unique_strategy_digest_count 1`
  - `summary.json` sets both export digest counts to `1`
  - retained result rows preserve `8` strategy digests, `8` export content digests, and `5` export structural digests
- retained interpretation:
  - high-value contradiction for archive history: headline digest counts cannot be trusted as a full diversity read

## Cluster 4: Heavy Park/Reject Burden Under Narrow Headline Totals
- archive meaning:
  - the final summary window is materially smaller than the semantic burden preserved in state
- bound evidence:
  - `summary.json` ends at `parked_total 2` and `rejected_total 2`
  - `state.json` keeps `park_set_len 13`, `reject_log_len 26`, `kill_log_len 6`, and `evidence_pending_len 4`
  - all `18` retained sim promotion states are `PARKED`
- retained interpretation:
  - useful archive evidence that final-window counters do not summarize total contradiction burden

## Cluster 5: A/Z Namespace Drift Inside One Run Family
- archive meaning:
  - the run preserves a live naming split between `A_` and `Z_` semantic ids inside the same retained state family
- bound evidence:
  - evidence-pending keys mix `A_CANON_*` and `Z_CANON_*`
  - sim ids mix `A_SIM_*` and `Z_SIM_*`
  - summary surfaces do not explain the prefix transition
- retained interpretation:
  - useful for demotion lineage because it shows semantic namespace drift without any corresponding promotion-law clarification

## Cluster 6: Full-Family Same-Name Strategy Divergence
- archive meaning:
  - consumed input residue and embedded transport residue are unstable by filename identity across the entire eight-packet family
- bound evidence:
  - consumed and embedded lanes both preserve `000001` through `000008`
  - all eight pairwise hash comparisons are mismatches
- retained interpretation:
  - this is stronger packet-lineage demotion evidence than the earlier runs because the divergence now spans an eight-packet family while the summary still collapses digest diversity to `1`

## Cluster 7: Missing Sim Evidence Bodies Despite Eight Sim Outputs
- archive meaning:
  - the run preserves strong SIM-result references without retaining the local evidence-text bodies they point at
- bound evidence:
  - retained result rows reference eight `SIM_TO_A0_SIM_RESULT_ZIP` outputs
  - event and soak rows point at runtime `sim/sim_evidence_*` paths
  - no local `sim/` directory exists in the archived run root
- retained interpretation:
  - the archive object is structurally useful but evidence-body incomplete

