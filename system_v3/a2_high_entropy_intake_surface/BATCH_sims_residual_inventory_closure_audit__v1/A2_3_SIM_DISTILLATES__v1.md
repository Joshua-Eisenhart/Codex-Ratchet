# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_residual_inventory_closure_audit__v1`
Extraction mode: `SIM_RESIDUAL_CLOSURE_AUDIT_PASS`

## Distillate D1
- strongest source-bound read:
  - the raw-order `simpy` family strip is exhausted, but residual sims-side coverage is not
- supporting anchors:
  - prior ultra sweep exhaustion manifest
  - current filename inventory totals

## Distillate D2
- strongest source-bound read:
  - `12` direct residual runner/result pairs still exist outside source membership
- supporting anchors:
  - current residual pair inventory
  - catalog visibility for many of those families

## Distillate D3
- strongest source-bound read:
  - `4` residual runners were already comparison-only anchors in earlier suite batches, which is different from source-membership coverage
- supporting anchors:
  - `BATCH_sims_sim_suite_v1_descendant_bundle__v1/MANIFEST.json`
  - `BATCH_sims_sim_suite_v2_successor_bundle__v1/MANIFEST.json`

## Distillate D4
- evidence assumptions extracted:
  - the catalog still lists many local residual families and result surfaces
  - the repo-held top-level evidence pack instead favors descendant or renamed SIM_IDs
  - direct source membership remains the narrowest practical coverage signal for this intake campaign
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - no additional raw-order `simpy` family batch remains
  - any future sims-side intake would have to reopen residual paired families, runner-only surfaces, or orphan result surfaces as a new priority campaign
  - this closure batch itself is filename-level only and does not execute or content-extract every residual file
- supporting anchors:
  - raw-order exhaustion read
  - closure-audit batch scope

## Distillate D6
- failure modes extracted:
  - claiming the sims source class is fully covered because raw-order intake ended
  - collapsing comparison-anchor reuse into direct source membership
  - treating orphan results, diagnostic scripts, cache files, or `.DS_Store` as if they were equivalent residual sim families
- supporting anchors:
  - tension items `T1` through `T7`
