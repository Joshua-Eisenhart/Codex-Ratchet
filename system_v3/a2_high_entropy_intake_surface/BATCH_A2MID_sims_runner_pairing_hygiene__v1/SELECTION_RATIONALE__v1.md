# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID BATCH SELECTION NOTE
Batch: `BATCH_A2MID_sims_runner_pairing_hygiene__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-08

## 1) Selected Parent Batch
Selected parent:
- `BATCH_sims_leading_space_runner_result_family__v1`

## 2) Why This Was The Next A2-Mid Target
Selection basis:
- it already existed as a packaged intake batch
- it is the first executable-facing sims family after the top-level boundary docs
- it exposes smaller reusable pairing and result-shape patterns without requiring any runtime execution

Why it is worth a bounded A2-mid pass now:
- the parent batch already separates three distinct runner/result families
- the strongest reusable content is executable pairing discipline rather than broad theory interpretation
- the main contradictions are already source-mapped and can be preserved cleanly

## 3) Why The Axis4 Family Was Deferred
Deferred next existing intake batch:
- `BATCH_sims_axis4_p03_core_harness_family__v1`

Reason for deferral:
- this pass finishes the first leading-space runner family before moving deeper into the next sims harness line
- the current parent batch gives cleaner immediate yield on pairing, compression-class splitting, and hygiene residue
- the Axis4 family remains the natural next existing sims reduction target

## 4) Narrowing Choice Inside The Selected Parent
This reduction batch deliberately keeps only:
- runner/result pairing and scope read
- deterministic knob and hashing pattern
- boundary-record compression split
- Axis12 bookkeeping vs Axis0 invariance split
- mega Stage16 vs Axis0 AB subfamily split
- direction-specific sequence-effect preservation

This reduction batch deliberately quarantines:
- leading-space runner path hazard
- deferred sidecar evidence reconciliation
- cross-axis causation overread from variant naming

## 5) Batch Result Type
Result type for this pass:
- sims executable pairing and hygiene reduction
- contradiction-preserving
- source-linked to the parent intake batch
- proposal-side only

This is not:
- a sidecar evidence reconciliation pass
- a runtime validation pass
- a proof of cross-axis causation
- an A2-1 promotion
