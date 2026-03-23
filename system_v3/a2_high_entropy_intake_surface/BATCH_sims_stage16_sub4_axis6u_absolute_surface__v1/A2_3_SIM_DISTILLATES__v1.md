# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_stage16_sub4_axis6u_absolute_surface__v1`
Extraction mode: `SIM_STAGE16_SUB4_AXIS6U_ABSOLUTE_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_stage16_sub4_axis6u.py` and `results_stage16_sub4_axis6u.json` form one bounded standalone Stage16 absolute baseline family
- supporting anchors:
  - raw-folder position
  - one runner plus one paired result surface

## Distillate D2
- strongest source-bound read:
  - the current result is the absolute baseline surface for the mixed-axis6 control family
- supporting anchors:
  - `results_stage16_axis6_mix_control.json` baseline comparison
  - maximum absolute mismatch only `1.1102230246251565e-16`

## Distillate D3
- strongest source-bound read:
  - the current local SIM_ID `S_SIM_STAGE16_SUB4_AXIS6U` is not repo-top admitted even though sibling Stage16 descendants are
- supporting anchors:
  - negative search for `S_SIM_STAGE16_SUB4_AXIS6U`
  - positive V4 / V5 evidence-pack blocks at `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`

## Distillate D4
- evidence assumptions extracted:
  - catalog presence includes the current Stage16 baseline and the adjacent terrain-only family
  - top-level evidence presence includes the V4 / V5 Stage16 descendants but not the current local SIM_ID
  - local executable richness is stronger than current top-level admission for this exact surface
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:104-146`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`

## Distillate D5
- runtime expectations extracted:
  - the current runner uses `512` random states, one qubit, one terrain order, and one fixed four-operator stack per stage
  - the output is a full absolute lattice with means and extrema
  - `Se` cells remain the most ordered and `Ne` cells the most mixed
- supporting anchors:
  - current runner contract
  - current result extrema

## Distillate D6
- failure modes extracted:
  - treating the current surface as if it were already evidenced at repo-top level
  - treating the V4 / V5 descendants as if they were the same output contract as the current local result
  - merging the adjacent `terrain8_sign_suite` into this batch because of raw-order proximity alone
- supporting anchors:
  - tension items `T1` through `T5`
