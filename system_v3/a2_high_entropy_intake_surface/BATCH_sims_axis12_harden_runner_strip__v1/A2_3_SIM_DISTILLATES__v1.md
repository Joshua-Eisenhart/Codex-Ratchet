# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_axis12_harden_runner_strip__v1`
Extraction mode: `SIM_AXIS12_HARDEN_RUNNER_STRIP_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly begins the runner-only residual-class campaign after paired-family completion
- supporting anchors:
  - closure audit manifest
  - current two-runner source membership

## Distillate D2
- strongest source-bound read:
  - the harden strip is a bundled multi-SIM producer class with six declared result files and six local SIM_IDs across `v1` and `v2`
- supporting anchors:
  - current runner headers
  - current emitted-write sections

## Distillate D3
- strongest source-bound read:
  - the closure-audit split between runner-only and result-only is operationally useful but semantically incomplete, because the runners explicitly declare the orphan result filenames as their own outputs
- supporting anchors:
  - closure audit manifest
  - current write contracts

## Distillate D4
- evidence assumptions extracted:
  - neither harden runner nor any harden-strip SIM_ID appears in the repo-held top-level catalog
  - neither harden runner nor any harden-strip SIM_ID appears in the repo-held top-level evidence pack
  - local evidence explicitness does not imply repo-top visibility
- supporting anchors:
  - negative substring search in `SIM_CATALOG_v1.3.md`
  - negative substring search in `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - `v1` writes three versioned result files plus one `sim_evidence_pack.txt`
  - `v2` writes three versioned result files plus one `sim_evidence_pack.txt`
  - both scripts use the same four-sequence axis12 lattice, the same `theta = 0.07`, and the same `3`-point sweep, but `v2` increases `num_states` from `256` to `512`
  - the shared evidence-pack filename is overwrite-prone across versions
- supporting anchors:
  - current runner bodies

## Distillate D6
- failure modes extracted:
  - mistaking the runner-only label for absence of declared outputs
  - treating `v2` as a cosmetic rename rather than a contract change
  - assuming repo-top omission means the harden strip is inactive or trivial
  - merging the six orphan result surfaces into this batch and breaking residual-class separation
  - missing the shared `sim_evidence_pack.txt` overwrite hazard
- supporting anchors:
  - tension items `T1` through `T6`
