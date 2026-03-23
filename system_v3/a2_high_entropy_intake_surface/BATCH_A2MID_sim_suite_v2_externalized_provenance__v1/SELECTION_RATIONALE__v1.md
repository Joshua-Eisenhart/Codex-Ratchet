# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED REFINEMENT RATIONALE
Batch: `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Why this parent batch was selected now
- it is the next strong sims intake family after the completed `sim_suite_v1` reduction
- the parent batch already isolates one sharp contradiction:
  - the current successor bundle emits seven descendants
  - all seven are repo-top evidenced
  - none of the seven is repo-top evidenced under the current successor-bundle hash
- its strongest seams are already narrow:
  - dedicated-runner externalization for Topology4, Axis4, and Axis0 V5
  - operator4 crossover back to the predecessor-bundle hash
  - Stage16 V5 byte identity against V4 under mega-hash provenance
  - malformed and foreign Negctrl provenance

## Why this reduction stays bounded
- it does not retell every descendant in full
- it keeps only the reusable packets needed later:
  - what `sim_suite_v2` emits
  - why its current repo-top provenance is externalized
  - where the operator4, Stage16, and Negctrl anomalies sit
  - why the next Stage16 family should remain separate

## Why no raw reread was needed
- the parent intake artifacts already preserve the seven-emission map, the zero current-hash match condition, and each externalized provenance mode explicitly
- the comparison anchors were sufficient for:
  - evidence coverage comparison
  - predecessor-bundle crossover comparison
  - operator4 provenance mismatch comparison

## What was explicitly deferred
- `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
  - remains the next separate sims family
  - was not merged into this successor-bundle reduction
- any claim that the current successor bundle is the strongest current top-level producer path for its emitted descendants
  - deferred because the parent batch preserves zero repo-top uses of the current bundle hash
- any claim that malformed or foreign hashes can be trusted as clean provenance
  - deferred because the parent batch explicitly preserves those as contradictions
