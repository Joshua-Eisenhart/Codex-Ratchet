# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID BATCH SELECTION NOTE
Batch: `BATCH_A2MID_sims_evidence_boundary__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-08

## 1) Selected Parent Batch
Selected parent:
- `BATCH_sims_top_level_docs_source_map__v1`

## 2) Why This Was The Next A2-Mid Target
Selection basis:
- it already existed as a packaged intake batch
- it is the root boundary document for the separate sims source lane
- it yields smaller reusable evidence and execution patterns without needing a raw rerun through the sims corpus

Why it is worth a bounded A2-mid pass now:
- the parent batch already separates catalog, runbook, and evidence roles cleanly
- the strongest reusable content is boundary-setting rather than family-specific theory
- the main contradictions are already mapped and can be preserved without inventing reconciliation

## 3) Why The Runner/Result Family Was Deferred
Deferred next existing intake batch:
- `BATCH_sims_leading_space_runner_result_family__v1`

Reason for deferral:
- this pass should first compress the top-level sims boundary docs into a cleaner admission/evidence lane surface
- runner/result pairing is better handled after the top-level boundary contract is reduced
- the leading-space runner batch remains the natural next executable-facing follow-up

## 4) Narrowing Choice Inside The Selected Parent
This reduction batch deliberately keeps only:
- separate sims source-class boundary
- catalog to runbook to evidence role chain
- hash-anchored `SIM_EVIDENCE` transport contract
- sharded failure isolation and negative-control discipline
- `simpy` harness root vs `simson` result root split

This reduction batch deliberately quarantines:
- filename-derived and runbook-embedded theory interpretation
- partial evidence-pack coverage relative to visible result files
- leading-space runner filenames and committed cache artifacts

## 5) Batch Result Type
Result type for this pass:
- sims evidence-lane and boundary reduction
- contradiction-preserving
- source-linked to the parent intake batch
- proposal-side only

This is not:
- a per-runner or per-result extraction pass
- a proof of sim-family behavior
- an A2-1 promotion
- a raw-doc reread
