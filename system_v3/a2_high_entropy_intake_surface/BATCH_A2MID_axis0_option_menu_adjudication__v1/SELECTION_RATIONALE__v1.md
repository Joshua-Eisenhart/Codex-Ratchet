# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID BATCH SELECTION NOTE
Batch: `BATCH_A2MID_axis0_option_menu_adjudication__v1`
Extraction mode: `QIT_BRIDGE_REDUCTION_PASS`
Date: 2026-03-08

## 1) Selected Parent Batch
Selected parent:
- `BATCH_refinedfuel_axis0_spec_options_qit_bridge__v1`

## 2) Why This Was The Next A2-Mid Target
Selection basis:
- it already existed as a packaged intake batch
- it is the direct elaboration of the prior Axis-0 bridge kernel
- it contains the first explicit candidate formula menu and staged sim ladder for Axis-0 in the refined-fuel lane

Why it is worth a bounded A2-mid pass now:
- the parent batch already isolates semantics, shared machinery, options, and sim ladder cleanly
- the strongest reusable content is the semantic lock plus option-adjudication structure, not the whole menu as one blob
- the main contradictions are already source-mapped and do not require raw reread

## 3) Why The v0.2 Options Batch Was Deferred
Deferred next existing intake batch:
- `BATCH_refinedfuel_axis0_spec_options_v02_qit_bridge__v1`

Reason for deferral:
- this pass first compresses the v0.1 option-menu kernel before comparing versions
- the parent batch gives immediate yield on how to hold multiple realizations under one semantic lock
- the v0.2 batch remains the natural next refinement target for narrowing or relabel comparison

## 4) Narrowing Choice Inside The Selected Parent
This reduction batch deliberately keeps only:
- Axis-0 semantic lock over option menu
- generic CPTP derivative index kernel
- low-complexity baseline option pair
- bounded advanced option family
- staged sim adjudication without a locked winner
- noncanon overlay subordination

This reduction batch deliberately quarantines:
- Option C as entropy-sign redefinition
- the whole option stack as already licensed kernel machinery
- Rosetta overlay as kernel vocabulary
- shell/cut clock candidates as primitive time

## 5) Batch Result Type
Result type for this pass:
- refined-fuel Axis-0 options reduction
- contradiction-preserving
- source-linked to the parent intake batch
- proposal-side only

This is not:
- a final winner-selection pass
- a sim-result pass
- raw-doc reread
- an A2-1 promotion
