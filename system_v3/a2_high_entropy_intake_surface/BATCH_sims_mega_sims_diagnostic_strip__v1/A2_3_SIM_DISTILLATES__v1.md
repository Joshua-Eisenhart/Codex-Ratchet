# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_mega_sims_diagnostic_strip__v1`
Extraction mode: `SIM_MEGA_SIMS_DIAGNOSTIC_STRIP_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch correctly groups the three `mega_sims_*` files into one bounded stochastic diagnostic strip
- supporting anchors:
  - current source membership
  - current shared-lane read

## Distillate D2
- strongest source-bound read:
  - `mega_sims_failure_detector.py` and `mega_sims_trivial_check.py` are near-duplicate boolean triviality detectors that reuse `E_MS_TRIVIAL`
- supporting anchors:
  - current boolean subcluster
  - current similarity ratio

## Distillate D3
- strongest source-bound read:
  - `mega_sims_run_02.py` expands the same lane into four always-signaled stress surfaces with metrics `collapse`, `vn_entropy_mean`, and `purity_min`
- supporting anchors:
  - current stress subcluster

## Distillate D4
- strongest source-bound read:
  - source-based inference says the whole strip preserves purity by construction because it evolves pure one-qubit states only by unitary conjugation
- supporting anchors:
  - current inference section

## Distillate D5
- evidence assumptions extracted:
  - the strip is local-script-visible only
  - it has no catalog admission
  - it has no repo-held evidence-pack admission
  - it has no committed `simson` result surfaces
- supporting anchors:
  - `SIM_CATALOG_v1.3.md`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - current directory inventory

## Distillate D6
- failure modes extracted:
  - deduplicating the two boolean detectors into one surface and losing the duplicated-token seam
  - treating `run_02` as a different physics family rather than a scaled diagnostic variant
  - overreading `collapse` as a live metric even though it is never updated
  - merging `prove_foundation.py` into the mega strip just because it also emits `SIM_EVIDENCE v1`
- supporting anchors:
  - tension items `T1` through `T6`
