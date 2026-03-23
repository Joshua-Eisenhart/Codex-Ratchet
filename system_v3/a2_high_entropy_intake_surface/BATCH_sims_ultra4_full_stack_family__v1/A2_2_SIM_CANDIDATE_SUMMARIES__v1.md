# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_ultra4_full_stack_family__v1`
Extraction mode: `SIM_ULTRA4_FULL_STACK_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `run_ultra4_full_stack.py` is the next unprocessed entrypoint and has one direct paired result surface
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at two sources:
    - one runner
    - one paired result
  - `ultra_axis0_ab_axis6_sweep` should remain comparison-only here
- supporting anchors:
  - batch selection and structural map

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “full-stack macro family with geometry, Stage16, Axis0 AB, and Axis12 layers under local-only evidence admission”
- supporting anchors:
  - current runner contract
  - negative evidence-pack match

## Candidate Summary C4
- proposal-only quarantine:
  - do not treat the `axis0_ab` branch as one uniform record type
- supporting anchors:
  - `SEQ01` absolute baselines versus `SEQ02` through `SEQ04` delta records

## Candidate Summary C5
- proposal-only quarantine:
  - do not collapse the Berry-flux layer into exact quantization or merge the adjacent ultra sweep into the same batch
- supporting anchors:
  - stored `berry_flux_plus` / `berry_flux_minus`
  - ultra sweep boundary

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_ultra_axis0_ab_axis6_sweep.py`, pair it with `results_ultra_axis0_ab_axis6_sweep.json`, and map it as the narrower ultra sweep family at the end of the current raw-order strip
- supporting anchors:
  - deferred next raw-folder-order source in this batch
