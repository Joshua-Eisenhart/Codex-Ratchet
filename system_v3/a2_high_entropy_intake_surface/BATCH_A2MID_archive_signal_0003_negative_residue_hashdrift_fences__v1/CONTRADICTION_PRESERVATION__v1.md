# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_signal_0003_negative_residue_hashdrift_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - accurate mid-scale accounting versus zero promotion passes
- kept explicit:
  - `summary.json` says:
    - `steps_completed 30`
    - `accepted_total 480`
    - unique digest counts of `30`
  - `events.jsonl` preserves thirty retained result rows over steps `1` through `30`
  - every promotion tier keeps zero passes
  - unresolved promotion blockers rise to `180`
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
    - `evidence_pending_len 30`
    - `kill_log_len 120`
    - `sim_promotion_status_len 180`
- why it must survive:
  - transport cleanliness is not semantic closure in this archive run

## Preserved contradiction 3
- headline:
  - final snapshot integrity versus event-lattice endpoint drift
- kept explicit:
  - `summary.json`, `state.json`, and `state.json.sha256` agree on final hash `d4b567...`
  - the last retained result row ends on `1aadd5...`
- why it must survive:
  - the run closes more strongly at the snapshot layer than at the event-lattice endpoint

## Preserved contradiction 4
- headline:
  - root sequence retention versus missing inbox-local sequence retention
- kept explicit:
  - root `sequence_state.json` survives with `A1 30`
  - `a1_inbox` contains only `consumed/`
  - `a1_inbox/sequence_state.json` is absent
- why it must survive:
  - the archive preserves real retention asymmetry and should not be smoothed into continuity

## Preserved contradiction 5
- headline:
  - negative residue inflation beyond ordinary SIM branch accounting
- kept explicit:
  - the run preserves six SIM outputs per step
  - the kill log still ends at `120`
  - negative tokens are duplicated through paired ids:
    - `S_SIM_NEG_A_*` with `S_MATH_ALT_A_*`
    - `S_SIM_NEG_B_*` with `S_MATH_ALT_B_*`
- why it must survive:
  - the parent's main new packet is that negative residue is larger and differently organized than the basic SIM branch count alone suggests

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
  - negative residue inflation as ordinary SIM branch accounting
  - runtime-like sim paths as proof that local evidence bodies were retained
