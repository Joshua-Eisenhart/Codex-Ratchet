# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / OUTER-CACHE DISTILLATE
Batch: `BATCH_sims_full_axis_suite_sampler_family__v1`
Extraction mode: `SIM_FULL_AXIS_SAMPLER_PASS`

## Distillate D1
- statement:
  - `full_axis_suite` is best read as a cross-axis sampler / precursor surface rather than one dedicated executable family
- source anchors:
  - `run_full_axis_suite.py:224-253`
  - `results_full_axis_suite.json:1-36`
- possible downstream consequence:
  - later sims interpretation can use it as a bridge map across multiple descendant families

## Distillate D2
- statement:
  - the sampler conceptually anticipates current standalone Axis3, Axis4, Axis5, and Axis6 descendants, but not as exact renamed outputs
- source anchors:
  - `results_full_axis_suite.json:1-36`
  - standalone descendant result surfaces read in this batch
- possible downstream consequence:
  - descendant linkage should stay proposal-side and axis-specific

## Distillate D3
- statement:
  - current top-level evidence has shifted fully to differently named descendants rather than the sampler’s emitted SIM_IDs
- source anchors:
  - `run_full_axis_suite.py:245-250`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- possible downstream consequence:
  - the sampler should not be over-promoted into current evidenced producer status

## Distillate D4
- statement:
  - Axis3 shows the closest continuity to the sampler, while Axis4 is the most divergent descendant in both naming and metric behavior
- source anchors:
  - `results_full_axis_suite.json:1-36`
  - `results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json:1-8`
  - `results_S_SIM_AXIS4_COMP_FETI_TEFI_CHECK_V1.json:1-6`
- possible downstream consequence:
  - later continuity summaries should rank descendant closeness rather than flatten it

## Distillate D5
- statement:
  - the sampler hash `71aa883f...` is not the code hash used by the current top-level evidenced descendants
- source anchors:
  - sampler hash in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- possible downstream consequence:
  - provenance claims must distinguish anticipation from direct authorship

## Distillate D6
- statement:
  - the next raw-order family should begin at `run_history_invariant_gradient_scan_v11.py` and be handled separately from this sampler
- source anchors:
  - deferred next raw-folder-order source in this batch
- possible downstream consequence:
  - the history-scan family can be processed without contaminating this cross-axis precursor read
