# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
Extraction mode: `SIM_STAGE16_AXIS6_MIX_FAMILY_PASS`

## Distillate D1
- strongest source-bound read:
  - `run_stage16_axis6_mix_control.py` and `run_stage16_axis6_mix_sweep.py` form one bounded Stage16 mixed-axis6 family
- supporting anchors:
  - raw folder adjacency
  - shared terrain order, axis6 patterning, operator family, and direct paired result files

## Distillate D2
- strongest source-bound read:
  - `run_stage16_sub4_axis6u.py` is the exact uniform-baseline anchor for this family, not the same bounded family
- supporting anchors:
  - exact identity of control `U_*` baselines to `sub4_axis6u` absolute means

## Distillate D3
- strongest source-bound read:
  - `mix_control` and `mix_sweep` ask the same theory-facing question but differ materially in executable comparison contract
- supporting anchors:
  - paired same-state control logic in `mix_control`
  - separate-stage-run and extra `MIX_R` logic in `mix_sweep`

## Distillate D4
- evidence assumptions extracted:
  - catalog admission is present for all three Stage16 surfaces
  - repo-top evidence-pack admission is absent for all three
  - local result richness is stronger than current top-level evidence strength
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:110-112`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - both mixed-axis6 scripts use `512` states, one qubit, one terrain order, one Stage16 cell lattice, and one `dS` / `dP` comparison surface
  - control yields smaller, more localized shifts
  - sweep expands to `MIX_A`, `MIX_B`, and `MIX_R`, producing larger cell-specific excursions
- supporting anchors:
  - source membership and result highlights in this batch

## Distillate D6
- failure modes extracted:
  - treating `sub4_axis6u` as if it were just another mixed-axis6 result
  - treating catalog presence as if it implied evidence-pack presence
  - flattening `mix_control` and `mix_sweep` into one equivalent numerical surface
- supporting anchors:
  - tension items `T1` through `T4`
