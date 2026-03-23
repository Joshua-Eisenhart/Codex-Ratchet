# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED REFINEMENT RATIONALE
Batch: `BATCH_A2MID_history_strip_provenance_asymmetry__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch was selected now
- it is the next strong sims intake family after the completed `full_axis_suite` reduction
- the parent batch already isolates one tight provenance problem:
  - many contiguous executable surfaces
  - one durable result surface
  - zero top-level evidence-pack blocks
- its strongest seams are already narrow:
  - `v11` current runner versus stored result mismatch
  - one-strip identity versus partial storage asymmetry
  - wrapper recursion and evidence-contract drift in the middle of the strip
  - catalog visibility versus missing top-level evidence admission

## Why this reduction stays bounded
- it does not retell every script in the strip
- it keeps only the reusable packets needed later:
  - what the strip is
  - how far the `v11` stored result outruns the live runner
  - where the runtime contract breaks inside the strip
  - how provenance confidence should be graded

## Why no raw reread was needed
- the parent intake artifacts already preserve the script/result mismatch, partial storage asymmetry, wrapper drift, and evidence gap explicitly
- the comparison anchors were sufficient for:
  - sims evidence-admission comparison
  - source-local-evidence versus repo-top-evidence comparison

## What was explicitly deferred
- `BATCH_sims_oprole8_left_right_harness_family__v1`
  - remains the next separate sims family
  - was not merged into this history-strip reduction
- any claim that the whole strip is fully evidenced
  - deferred because the parent batch preserves only one durable result surface and no top-level evidence-pack blocks
- any claim that the current `v11` runner is the exact producer of the stored depth curve
  - deferred because the parent batch preserves a direct code-hash mismatch
