# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0002__v1`
Date: 2026-03-09

## Cluster 1: Queue-Drained Direct Autoratchet Run
- archive meaning:
  - this object preserves a direct QIT autoratchet run after the strategy queue was fully consumed, not a live-backlog snapshot and not a wrapper bundle
- bound evidence:
  - `a1_inbox/consumed/` contains five strategy packets
  - no live strategy packet files remain in `a1_inbox/`
  - no wrapper README or `HARDMODE_METRICS.json` is present
- retained interpretation:
  - useful as historical evidence of a drained-but-unresolved autoratchet run rather than a clean completed milestone

## Cluster 2: Single-Step Compression Over Five Retained Passes
- archive meaning:
  - the run surface collapses repeated result passes into one nominal completed step
- bound evidence:
  - `summary.json` says `steps_completed 1`
  - `events.jsonl` keeps five `step_result` rows
  - all retained result rows use step value `1`
- retained interpretation:
  - this archive object should be read as repeated step-one replay compressed into one headline step, not as a literal one-pass run

## Cluster 3: Deep Semantic Burden Under Narrow Counters
- archive meaning:
  - the summary window is much smaller than the semantic residue preserved in final state
- bound evidence:
  - `summary.json` says `parked_total 1` and `rejected_total 10`
  - `state.json` keeps `park_set_len 3`, `reject_log_len 33`, `kill_log_len 4`, and `evidence_pending_len 2`
  - all `13` `sim_promotion_status` entries are `PARKED`
- retained interpretation:
  - good archive evidence that headline counters should not be mistaken for the total retained contradiction burden

## Cluster 4: Dual Sequence Views With Partial Agreement
- archive meaning:
  - the run keeps both a full transport sequence ledger and a narrower inbox-local A1 sequence ledger
- bound evidence:
  - root `sequence_state.json` records `A1 5` alongside other sources
  - `a1_inbox/sequence_state.json` records `RUN_QIT_AUTORATCHET_0002|A1 -> 5`
  - the JSON bodies are not identical
- retained interpretation:
  - useful for lineage because it shows sequence agreement on A1 while still preserving surface-shape mismatch across ledgers

## Cluster 5: Total Same-Name Strategy Packet Divergence
- archive meaning:
  - consumed input residue and embedded transport residue are maximally unstable by filename identity alone
- bound evidence:
  - consumed and embedded lanes both preserve `000001` through `000005`
  - all five pairwise hash comparisons are mismatches
- retained interpretation:
  - this is stronger demotion evidence than the prior `0001` run because no same-name strategy packet pair survives byte-identically

