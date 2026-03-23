# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED REFINEMENT RATIONALE
Batch: `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch was selected now
- it is the next strong sims intake family after the completed `oprole8` reduction
- the parent batch already isolates one high-value contradiction:
  - one bundle emits ten descendants
  - repo-top evidence covers all ten
  - current provenance does not remain on one bundle hash
- its strongest seams are already narrow:
  - aligned four-descendant subset
  - migrated six-descendant subset
  - Stage16 byte-identity despite version drift
  - Negctrl crossover into successor-bundle hash territory
  - explicit non-merge boundary with `sim_suite_v2`

## Why this reduction stays bounded
- it does not retell each descendant in full
- it keeps only the reusable packets needed later:
  - what the bundle emits
  - how provenance splits
  - which parts still align
  - where version and producer continuity separate

## Why no raw reread was needed
- the parent intake artifacts already preserve the emission map, evidence coverage, hash split, and version drift explicitly
- the comparison anchors were sufficient for:
  - evidence-coverage comparison
  - cross-family `run_sim_suite_v1.py` hash mismatch comparison
  - Axis4 dedicated-lineage comparison

## What was explicitly deferred
- `BATCH_sims_sim_suite_v2_successor_bundle__v1`
  - remains the next separate sims family
  - was not merged into this reduction
- any claim that one current producer path governs all ten descendants
  - deferred because the parent batch explicitly preserves six-way current provenance split
- any claim that version labels alone settle payload change
  - deferred because the parent batch preserves Stage16 byte identity and Negctrl metric continuity under version drift
