# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V2_RESULT_ORPHAN_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly reopens the deferred harden `v2` successor triplet after the `v1` result-only batch
- supporting anchors:
  - prior `v1` orphan batch manifest
  - current three source members

## Distillate D2
- strongest source-bound read:
  - `paramsweep_v2` keeps a robust positive `seni` partition signal across all six rows
- supporting anchors:
  - current `paramsweep_v2` row summaries

## Distillate D3
- strongest source-bound read:
  - `altchan_v2` remains effectively collapsed, with exact zeros on four rows and only near-zero weak-row residuals
- supporting anchors:
  - current `altchan_v2` row summaries

## Distillate D4
- strongest source-bound read:
  - `negctrl_label_v2` is a real dynamic successor control that is mostly opposite in sign to the base-channel surface
- supporting anchors:
  - current `negctrl_label_v2` row summaries
  - current `paramsweep_v2` row summaries

## Distillate D5
- evidence assumptions extracted:
  - the `v2` triplet is listed in the top-level catalog by filename alias only
  - none of the three filenames or three local SIM_IDs appears in the repo-held top-level evidence pack
  - current source membership stays result-only even though the producer-side linkage is explicit
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - prior runner-only batch manifest

## Distillate D6
- failure modes extracted:
  - mistaking filename-level catalog visibility for evidence-pack admission
  - treating the compressed successor schema as if it still preserved sequence-level explanations
  - overreading the tiny weak-row sign flip in `altchan_v2`
  - describing `negctrl_label_v2` as a no-op control when it is a dynamic, mostly inverted surface
  - collapsing `v1` and `v2` into one harden result batch
- supporting anchors:
  - tension items `T1` through `T6`
