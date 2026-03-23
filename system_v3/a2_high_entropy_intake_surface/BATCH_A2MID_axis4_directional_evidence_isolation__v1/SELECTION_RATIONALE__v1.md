# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION NOTE
Batch: `BATCH_A2MID_axis4_directional_evidence_isolation__v1`
Date: 2026-03-09

## Why this parent batch was selected
- it is the next strong sims intake batch after the graph-prompt reduction
- it already cleanly exposes:
  - directional runner/result family structure
  - a separate theory-facing aggregate sibling
  - top-level evidence-pack producer mismatch
  - direction-labeled blocks that still carry both directions
  - partial Type-2 evidence coverage
  - branch-specific signal separation between plus and minus
- that makes it a strong bounded evidence-isolation reduction target without rereading raw sims artifacts

## Why this reduction is bounded
- the pass keeps only the smaller reusable packets:
  - executable/theory/evidence split for the directional suite
  - runner/result pairing with producer-hash suspension
  - direction label does not equal direction-isolated evidence
  - aggregate minus-only compression layer
  - Type-2 result presence with top-level evidence gap
  - plus-branch inertia versus minus-branch signal split
- the pass does not reopen raw catalog or evidence-pack content beyond the parent batch's extracted comparisons

## Why comparison anchors were used
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it gives the nearest sims-wide evidence transport and hash-boundary contract
- `BATCH_A2MID_sims_axis4_p03_evidence_path__v1`
  - used because it gives the nearest earlier Axis4 result-to-evidence alignment packet and branch-specific sequence read
- `BATCH_A2MID_sims_runner_pairing_hygiene__v1`
  - used because it gives the nearest pairing hygiene and directional anti-flattening packet

## Why no raw reread was needed
- the parent batch already extracted the relevant runner/result/evidence lineage and the explicit contradiction markers
- the needed work here was second-pass narrowing and quarantine, not source recovery

## Deferred alternatives
- `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
  - deferred to the next bounded step because this directional suite is the tighter evidence-isolation unit and the parent batch already points raw order onward to `run_batch_v3.py`
- `fresh_raw_axis4_directional_suite_reread`
  - deferred because this thread prefers existing intake artifacts unless the parent batch is insufficient
