# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
Extraction mode: `SIM_BATCH_BUNDLE_PASS`

## Distillate D1
- statement:
  - `run_batch_v3.py` is best read as a composite precursor bundle rather than one present-tense executable family
- source anchors:
  - `run_batch_v3.py:435-500`
  - `results_batch_v3.json:1-222`
- possible downstream consequence:
  - later sims intake should use this batch mainly for lineage and packaging structure

## Distillate D2
- statement:
  - the bundle's evidence model is payload-level, not aggregate-file-level
- source anchors:
  - `run_batch_v3.py:416-433`
  - `run_batch_v3.py:487-498`
  - `results_batch_v3.json:1-222`
- possible downstream consequence:
  - provenance work should track the four embedded output hashes separately from the aggregate result file hash

## Distillate D3
- statement:
  - the current repo foregrounds later standalone descendants of the bundle, not the bundle's own V3/V1 SIM_IDs
- source anchors:
  - `SIM_CATALOG_v1.3.md:39-54`
  - `SIM_CATALOG_v1.3.md:102-108`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:2-40`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-414`
- possible downstream consequence:
  - this batch should remain proposal-side and source-historical rather than being over-promoted into current evidence authority

## Distillate D4
- statement:
  - descendant drift from the bundle is uneven: Axis12 becomes a grid, Axis0 is reshaped, Stage16 duplicates by name with identical bytes, and Negctrl revises trials while keeping zero means
- source anchors:
  - the seven descendant result surfaces read in this batch
- possible downstream consequence:
  - family-specific lineage mapping is safer than one generic “V3 to V4/V5 upgrade” story

## Distillate D5
- statement:
  - `run_engine32_axis0_axis6_attack.py` should be kept out of this batch even though it is the adjacent raw-order source
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:168-238`
  - `results_engine32_axis0_axis6_attack.json:1-689`
  - `SIM_CATALOG_v1.3.md:54`
  - `SIM_CATALOG_v1.3.md:102`
- possible downstream consequence:
  - the next pass can process `engine32` cleanly as its own direct executable family
