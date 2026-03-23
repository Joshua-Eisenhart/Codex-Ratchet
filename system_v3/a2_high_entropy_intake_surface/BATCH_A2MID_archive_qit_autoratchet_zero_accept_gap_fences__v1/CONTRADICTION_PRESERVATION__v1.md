# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_qit_autoratchet_zero_accept_gap_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - zero-accept headline versus accepted first step
- kept explicit:
  - `summary.json` and `soak_report.md` preserve `accepted_total 0`
  - `state.json` preserves `accepted_batch_count 1` and `canonical_ledger_len 1`
  - `events.jsonl` preserves one `step_result` row with `accepted 7`
- why it must survive:
  - the parent's main historical contradiction is accounting, and it should not be smoothed into either failure-only or success-only language

## Preserved contradiction 2
- headline:
  - explicit sequence ledger versus repeated sequence-gap failure
- kept explicit:
  - `sequence_state.json` is retained
  - four `a1_generation_fail` rows preserve `a1_packet_zip_invalid::SEQUENCE_GAP`
  - active inbox still holds packets `000002` through `000005`
- why it must survive:
  - explicit sequence tracking did not prevent queue-gap failure in this run

## Preserved contradiction 3
- headline:
  - packet cleanliness versus parked semantic outcomes
- kept explicit:
  - `parked_total 0`
  - `rejected_total 0`
  - both sims marked `PARKED`
  - one canonical evidence item pending
  - two `NEG_INFINITE_SET` kill signals
- why it must survive:
  - packet-level cleanliness and semantic promotion state are not the same layer

## Preserved contradiction 4
- headline:
  - same filename versus different bytes on packet `000001`
- kept explicit:
  - consumed packet `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - embedded packet `000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - filenames match
  - hashes differ
- why it must survive:
  - packet identity cannot be inferred from filename alone here

## Preserved contradiction 5
- headline:
  - strong state integrity versus missing local evidence bodies
- kept explicit:
  - `state.json` hash matches `summary.json` final state hash
  - events and soak still reference local `sim/sim_evidence_*`
  - no local `sim/` subtree is retained
- why it must survive:
  - structural integrity outlives evidence-body preservation in this archive object

## Non-preserved overreads
- not preserved:
  - the run as active runtime or wrapped export authority
  - the zero-accept headline as the whole truth
  - the sequence ledger as proof that sequence control worked
  - zero packet parks/rejects as no semantic burden
  - shared filename as packet identity equivalence
