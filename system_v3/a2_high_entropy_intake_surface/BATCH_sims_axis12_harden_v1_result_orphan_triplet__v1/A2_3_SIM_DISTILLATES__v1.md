# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V1_RESULT_ORPHAN_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly reopens the first deferred harden result triplet from the prior runner-only strip
- supporting anchors:
  - prior runner-only batch manifest
  - current three source members

## Distillate D2
- strongest source-bound read:
  - `paramsweep_v1` is the only surface in the current triplet that preserves a clear stored `seni` partition signal
- supporting anchors:
  - current `paramsweep_v1` row summaries

## Distillate D3
- strongest source-bound read:
  - `altchan_v1` uses the same result schema as `paramsweep_v1` but almost entirely collapses to maximum mixing and near-zero separation
- supporting anchors:
  - current `altchan_v1` row summaries

## Distillate D4
- strongest source-bound read:
  - `negctrl_swap_v1` is a purely combinatorial control whose swapped booleans are observationally identical to the original booleans on this four-sequence lattice
- supporting anchors:
  - current `negctrl_swap_v1` flags
  - current `paramsweep_v1` flags

## Distillate D5
- evidence assumptions extracted:
  - the triplet is listed in the top-level catalog by filename alias only
  - none of the three filenames or three local SIM_IDs appears in the repo-held top-level evidence pack
  - current source membership stays result-only even though the producer-side linkage is explicit
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - prior runner-only batch manifest

## Distillate D6
- failure modes extracted:
  - mistaking filename-level catalog visibility for evidence-pack admission
  - treating `altchan_v1` as corroboration of the base-channel `seni` split
  - overstating `negctrl_swap_v1` as a visible reversal when the stored booleans do not change
  - collapsing the triplet into a homogeneous all-dynamic family
  - merging `v2` orphan surfaces into this `v1` batch
- supporting anchors:
  - tension items `T1` through `T6`
