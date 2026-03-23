# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_ladder_seed_action_name_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - clean parked/reject totals versus retained negative seam
- kept explicit:
  - `parked_total 0`
  - `rejected_total 0`
  - soak failure tags `NONE`
  - `kill_log_len 1`
  - `unresolved_promotion_blocker_count 1`
- why it must survive:
  - the run is tidy but not failure-free, and that asymmetry is the parent's sharpest reusable contradiction

## Preserved contradiction 2
- headline:
  - semantic action naming versus protocol packet naming
- kept explicit:
  - consumed input:
    - `000001_FND_LR_ACTION.zip`
  - embedded packet:
    - `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - both surfaces preserve identical bytes
- why it must survive:
  - the archive stores one payload under two naming grammars without resolving which grammar should dominate later interpretation

## Preserved contradiction 3
- headline:
  - strong integrity residue versus missing evidence bodies
- kept explicit:
  - final state hash matches across `summary.json`, `state.json`, and `state.json.sha256`
  - event and soak surfaces still reference local `sim/sim_evidence_*`
  - no local `sim/` directory is retained
- why it must survive:
  - integrity and packet proof outlast the evidence-body layer, and that retention asymmetry should not be flattened

## Non-preserved overreads
- not preserved:
  - the run as active runtime authority
  - the run as fully failure-free
  - one packet naming regime as uniquely authoritative
  - retained path references as proof that evidence bodies survived
  - the ladder seed as equivalent to later bundle/export artifacts
