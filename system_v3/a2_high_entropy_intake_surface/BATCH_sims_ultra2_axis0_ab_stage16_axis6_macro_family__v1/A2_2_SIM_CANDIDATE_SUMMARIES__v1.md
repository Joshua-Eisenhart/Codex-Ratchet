# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1`
Extraction mode: `SIM_ULTRA2_MACRO_BUNDLE_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_ultra2_axis0_ab_stage16_axis6.py` is the next unprocessed entrypoint and has one direct paired result surface
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - `ultra4` should remain comparison-only here
- supporting anchors:
  - batch selection and structural map

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “macro composite family with three internal branches and local-only evidence admission”
- supporting anchors:
  - current runner contract
  - negative evidence-pack match

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat the stored `seqs` field as complete for Axis12 interpretation
- supporting anchors:
  - hidden `SEQ03` / `SEQ04` counts in the stored `axis12` object

## Candidate Summary C5
- proposal-only quarantine:
  - do not collapse `ultra2` into `ultra4` or speak about one single macro effect scale across all ultra2 branches
- supporting anchors:
  - stage16 / axis0 branch magnitude contrast
  - ultra4 expansion boundary

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_ultra4_full_stack.py`, pair it with `results_ultra4_full_stack.json`, and map it as the expanded full-stack macro family before raw order advances to `run_ultra_axis0_ab_axis6_sweep.py`
- supporting anchors:
  - deferred next raw-folder-order source in this batch
