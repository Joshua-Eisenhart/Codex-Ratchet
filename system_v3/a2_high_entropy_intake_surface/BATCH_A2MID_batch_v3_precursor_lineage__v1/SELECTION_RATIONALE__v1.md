# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION NOTE
Batch: `BATCH_A2MID_batch_v3_precursor_lineage__v1`
Date: 2026-03-09

## Why this parent batch was selected
- it is the next strong sims intake batch after the Axis4 directional evidence-isolation reduction
- it already cleanly exposes:
  - one composite precursor bundle rather than one present-tense executable family
  - per-subpayload evidence hashing inside one aggregate container
  - a shift from bundle-local V3/V1 SIM_IDs to later standalone descendants
  - uneven descendant drift across Axis12, Axis0, Stage16, and Negctrl
  - duplicate-label residue inside Stage16 descendants
  - explicit separation from adjacent `engine32`
- that makes it a strong bounded lineage and packaging reduction target without rereading raw sims artifacts

## Why this reduction is bounded
- the pass keeps only the smaller reusable packets:
  - precursor-bundle nonauthority
  - per-subpayload hashing over aggregate container
  - bundle-local IDs to standalone descendant evidence shift
  - family-specific descendant drift
  - Stage16 duplicate-label same-bytes residue
  - adjacent `engine32` separation
- the pass does not try to re-interpret the embedded metrics as if `batch_v3` were a clean current evidence family

## Why comparison anchors were used
- `BATCH_A2MID_sims_evidence_boundary__v1`
  - used because it gives the nearest existing sims-wide evidence transport contract for the parent's per-payload hashing seam
- `BATCH_A2MID_axis4_directional_evidence_isolation__v1`
  - used because it gives the nearest producer/container/evidence split and provenance-suspension packet
- `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
  - used because the parent explicitly defers `engine32` as the next separate executable family rather than merging it into the precursor bundle

## Why no raw reread was needed
- the parent batch already extracted the bundle structure, lineage shift, and descendant drift markers
- the needed work here was narrower lineage reduction and quarantine, not source recovery

## Deferred alternatives
- `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
  - deferred to the next bounded step because the parent batch explicitly frames `engine32` as the adjacent excluded family and the natural next raw-order source
- `fresh_raw_batch_v3_reread`
  - deferred because this thread prefers existing intake artifacts unless the parent batch is insufficient
