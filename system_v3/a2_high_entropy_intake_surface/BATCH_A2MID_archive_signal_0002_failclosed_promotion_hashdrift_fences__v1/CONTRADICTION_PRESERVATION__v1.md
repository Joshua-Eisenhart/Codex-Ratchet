# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_signal_0002_failclosed_promotion_hashdrift_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - accurate large-run accounting versus zero promotion passes
- kept explicit:
  - `summary.json` says:
    - `steps_completed 50`
    - `accepted_total 700`
    - unique digest counts of `50`
  - `events.jsonl` preserves fifty retained result rows over steps `1` through `50`
  - every promotion tier keeps zero passes
  - unresolved promotion blockers rise to `300`
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
    - `evidence_pending_len 50`
    - `kill_log_len 100`
    - `sim_promotion_status_len 300`
- why it must survive:
  - transport cleanliness is not semantic closure in this archive run

## Preserved contradiction 3
- headline:
  - final snapshot integrity versus event-lattice endpoint drift
- kept explicit:
  - `summary.json`, `state.json`, and `state.json.sha256` agree on final hash `3d779f...`
  - the last retained result row ends on `496d384...`
- why it must survive:
  - the run closes more strongly at the snapshot layer than at the event-lattice endpoint

## Preserved contradiction 4
- headline:
  - root sequence retention versus missing inbox-local sequence retention
- kept explicit:
  - root `sequence_state.json` survives with `A1 50`
  - `a1_inbox` contains only `consumed/`
  - `a1_inbox/sequence_state.json` is absent
- why it must survive:
  - the archive preserves real retention asymmetry and should not be smoothed into continuity

## Preserved contradiction 5
- headline:
  - embedded strategy naming versus consumed strategy naming
- kept explicit:
  - embedded strategy packets use `000001` through `000050`
  - consumed strategy packets use `400001` through `400050`
  - only the first same-position pair is byte-identical
  - the other forty-nine same-position pairs diverge byte-for-byte
- why it must survive:
  - naming discontinuity and dominant byte mismatch are the real packet-lineage lesson here

## Preserved contradiction 6
- headline:
  - runtime-like sim evidence paths versus no local sim subtree
- kept explicit:
  - retained SIM outputs point at concrete `sim/sim_evidence_*` paths
  - the archive run root contains no local `sim/` directory
- why it must survive:
  - this run preserves structurally rich evidence references without preserving local evidence bodies

## Non-preserved overreads
- not preserved:
  - accurate counters as proof that promotion succeeded
  - zero packet parks/rejects as proof of no semantic burden
  - last retained event hash as proof of full run closure
  - root sequence retention as proof of inbox-local sequence continuity
  - renamed consumed strategy files as proof of full embedded-lane equivalence
  - runtime-like sim paths as proof that local evidence bodies were retained
