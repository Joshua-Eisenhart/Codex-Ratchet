# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_sim_suite_v2_successor_bundle__v1`
Extraction mode: `SIM_SUITE_V2_SUCCESSOR_BUNDLE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_sim_suite_v2_full_axes.py` is a coherent successor bundle that currently emits seven stored descendant surfaces
- supporting anchors:
  - `run_sim_suite_v2_full_axes.py:423-460`
  - batch source membership

## Distillate D2
- strongest source-bound read:
  - all seven emitted descendants are repo-top evidenced, but none is repo-top evidenced under the current successor-bundle hash `dd05c8f6...`
- supporting anchors:
  - top-level evidence blocks for the seven emitted SIM_IDs

## Distillate D3
- strongest source-bound read:
  - repo-top provenance has fully externalized away from the current bundle into:
    - dedicated topology / axis / axis0 runners
    - the predecessor bundle hash
    - the leading-space mega hash
    - an all-zero placeholder hash
    - a cross-family leading-space hash
- supporting anchors:
  - evidence-pack code hashes and current hash matches in this batch

## Distillate D4
- strongest source-bound read:
  - the successor bundle still matters executable-facingly because it is the current emitter of:
    - Topology4 Terrain8 V1
    - Axis4 comp check V1
    - Axis56 operator4 LR V1
    - Stage16 V5
    - Axis0 V5
    - Negctrl Axis6 V3
    - Negctrl Axis0 NoEnt V1
- supporting anchors:
  - `run_sim_suite_v2_full_axes.py:423-460`

## Distillate D5
- runtime expectations extracted:
  - topology4 terrain8, axis4 comp check, and operator4 LR use `512` trials
  - Stage16 uniform Axis6, Axis0 V5, and Negctrl Axis0 NoEnt use `256`-trial-class settings
  - Negctrl Axis6 V3 uses `512` trials
  - Axis0 V5 is a two-sequence, `64`-cycle, entangled-init delta suite
  - Negctrl Axis0 NoEnt is a `32`-cycle, no-entangler, non-entangled-init delta suite
- supporting anchors:
  - sim definitions in `run_sim_suite_v2_full_axes.py`

## Distillate D6
- failure modes extracted:
  - treating the current successor bundle as the strongest evidenced producer path for its emitted descendants
  - flattening the cross-bundle operator4 seam into a clean upgrade from `sim_suite_v1`
  - treating all-zero or cross-family code hashes as if they were trustworthy provenance
  - assuming V5 labels imply changed Stage16 payloads without checking stored outputs
- supporting anchors:
  - tension items `T1` through `T8`
