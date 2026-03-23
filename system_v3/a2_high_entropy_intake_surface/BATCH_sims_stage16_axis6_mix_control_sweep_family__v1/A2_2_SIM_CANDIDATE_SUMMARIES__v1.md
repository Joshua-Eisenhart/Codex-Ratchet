# A2_2_SIM_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / INTERMEDIATE CANDIDATE SUMMARY
Batch: `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
Extraction mode: `SIM_STAGE16_AXIS6_MIX_FAMILY_PASS`

## Candidate Summary C1
- proposal-only reading:
  - this is the correct next raw-order batch because `mix_control` is the next unprocessed entrypoint and `mix_sweep` is its direct Stage16 sibling with a matching paired result surface
- supporting anchors:
  - batch source membership

## Candidate Summary C2
- proposal-only reading:
  - the bounded family should stay at four sources:
    - two runners
    - two paired results
  - `sub4_axis6u` should remain comparison-only
- supporting anchors:
  - batch selection and structural map

## Candidate Summary C3
- proposal-only reading:
  - the strongest interpretation is “Stage16 mixed-axis6 comparison family built on the `sub4_axis6u` baseline”
- supporting anchors:
  - exact baseline identity from `sub4_axis6u`

## Candidate Summary C4
- proposal-only quarantine:
  - do not infer top-level evidence strength for this family from catalog presence alone
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:110-112`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Candidate Summary C5
- proposal-only quarantine:
  - do not treat `mix_control` as numerically interchangeable with the corresponding `MIX_A` / `MIX_B` cells in `mix_sweep`
- supporting anchors:
  - executable contract difference in this batch

## Candidate Summary C6
- proposal-only next-step note:
  - the next bounded sims batch should start at `run_stage16_sub4_axis6u.py`, pair it with `results_stage16_sub4_axis6u.json`, and map it as the absolute Stage16 baseline family before the raw-order flow moves on to `run_terrain8_sign_suite.py`
- supporting anchors:
  - deferred next raw-folder-order source in this batch
