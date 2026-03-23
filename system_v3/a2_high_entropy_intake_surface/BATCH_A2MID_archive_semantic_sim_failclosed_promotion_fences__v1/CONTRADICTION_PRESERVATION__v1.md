# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_semantic_sim_failclosed_promotion_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - accurate summary accounting versus zero promotion passes
- kept explicit:
  - `summary.json` says:
    - `steps_completed 5`
    - `accepted_total 70`
    - unique digest counts of `5`
  - `events.jsonl` preserves five retained result rows over steps `1` through `5`
  - `promotion_counts_by_tier` still record only failures and zero passes
  - all `30` sim promotion states remain `PARKED`
- why it must survive:
  - the parent's main archive value is that correct accounting still does not imply promotion truth

## Preserved contradiction 2
- headline:
  - zero packet parks/rejects versus large semantic burden
- kept explicit:
  - packet-facing surfaces end at:
    - `parked_total 0`
    - `rejected_total 0`
  - `state.json` still keeps:
    - `evidence_pending_len 5`
    - `kill_log_len 10`
    - `sim_promotion_status_len 30`
- why it must survive:
  - transport cleanliness is not semantic closure in this archive run

## Preserved contradiction 3
- headline:
  - root sequence retention versus missing inbox-local sequence retention
- kept explicit:
  - root `sequence_state.json` survives with `A1 5`
  - `a1_inbox` contains only `consumed/`
  - `a1_inbox/sequence_state.json` is absent
- why it must survive:
  - the archive preserves a real retention asymmetry and should not be smoothed into continuity

## Preserved contradiction 4
- headline:
  - embedded strategy naming versus consumed strategy naming
- kept explicit:
  - embedded strategy packets use `000001` through `000005`
  - consumed strategy packets use `400001` through `400005`
  - only the first consumed packet is byte-identical to an embedded packet
  - the other four consumed packets have no embedded byte-identical match
- why it must survive:
  - naming discontinuity and partial byte overlap are the real packet-lineage lesson here

## Preserved contradiction 5
- headline:
  - runtime-like sim evidence paths versus no local sim subtree
- kept explicit:
  - retained SIM outputs point at concrete `sim/sim_evidence_*` paths
  - the archive run root contains no local `sim/` directory
- why it must survive:
  - this run preserves structurally rich evidence references without preserving the local evidence bodies

## Non-preserved overreads
- not preserved:
  - accurate counters as proof that promotion succeeded
  - zero packet parks/rejects as proof of no semantic burden
  - root sequence retention as proof of inbox-local sequence continuity
  - renamed consumed strategy files as proof of full embedded-lane equivalence
  - runtime-like sim paths as proof that local evidence bodies were retained
