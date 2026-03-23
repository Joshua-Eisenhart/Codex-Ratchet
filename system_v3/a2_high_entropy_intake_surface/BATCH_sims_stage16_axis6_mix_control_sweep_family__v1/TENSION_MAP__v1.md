# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_stage16_axis6_mix_control_sweep_family__v1`
Extraction mode: `SIM_STAGE16_AXIS6_MIX_FAMILY_PASS`

## T1) `mix_control` and `mix_sweep` are the same question-family but different executable contracts
- source markers:
  - `run_stage16_axis6_mix_control.py:1-217`
  - `run_stage16_axis6_mix_sweep.py:1-219`
- tension:
  - both scripts compare mixed intra-stage axis6 behavior against a uniform baseline
  - `mix_control` runs one mixed pattern and reuses the same `rho0` for paired control vs mixed comparison
  - `mix_sweep` runs three mix modes and samples uniform and mixed via separate stage runs
- preserved read:
  - do not collapse them into “same computation, more modes”
- possible downstream consequence:
  - later summaries should distinguish paired-control results from sweep results

## T2) `sub4_axis6u` is raw-order adjacent and baseline-identical to control, but it is not the same bounded family
- source markers:
  - `run_stage16_sub4_axis6u.py:1-228`
  - `results_stage16_axis6_mix_control.json`
  - `results_stage16_sub4_axis6u.json`
- tension:
  - every `U_Smean` and `U_Pmean` value in control matches the absolute `sub4_axis6u` means exactly
  - `sub4_axis6u` does not compare any mixed patterns
- preserved read:
  - keep `sub4_axis6u` as the exact baseline anchor, not as a merged family member
- possible downstream consequence:
  - the next batch can treat `sub4_axis6u` as its own absolute Stage16 surface

## T3) Catalog groups the Stage16 trio, but the top-level evidence pack admits none of them
- source markers:
  - `SIM_CATALOG_v1.3.md:110-112`
  - `SIM_CATALOG_v1.3.md:143-145`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog explicitly names `mix_control`, `mix_sweep`, and `sub4_axis6u`
  - the repo-held top-level evidence pack contains no matching SIM_ID blocks for any of the three
- preserved read:
  - keep catalog admission distinct from evidence-pack admission
- possible downstream consequence:
  - this family should stay proposal-side in provenance strength

## T4) Control effects are small and localized, while sweep effects are larger and mode-sensitive
- source markers:
  - `results_stage16_axis6_mix_control.json`
  - `results_stage16_axis6_mix_sweep.json`
- tension:
  - control max absolute `dS` is about `0.0031794665`
  - sweep max absolute `dS` reaches `0.01229781198`
  - sweep max absolute `dP` reaches `0.01041681746`
- preserved read:
  - do not summarize the family as one uniform perturbation scale
- possible downstream consequence:
  - later interpretation should preserve that sweep mode choice can dominate stagewise effect size

## T5) Some stages remain near-zero under control while sweep introduces nontrivial movement
- source markers:
  - `results_stage16_axis6_mix_control.json`
  - `results_stage16_axis6_mix_sweep.json`
- tension:
  - control leaves several `Ne` and `Si` cells exactly or nearly unchanged
  - sweep introduces measurable `MIX_A` / `MIX_B` / `MIX_R` offsets in those same regions
- preserved read:
  - keep stage-specific sensitivity uneven rather than speaking about one blanket Stage16 response
- possible downstream consequence:
  - later Stage16 work should be stage-cell specific, not family-average only

## T6) The strongest sweep cell is Type2 inner `4_Si_DOWN`, not the same Se-focused region that dominates control
- source markers:
  - `results_stage16_axis6_mix_control.json`
  - `results_stage16_axis6_mix_sweep.json`
- tension:
  - control’s largest shifts sit in `1_Se_*` cells
  - sweep’s largest absolute shifts sit in `type2.inner.4_Si_DOWN`, especially under `MIX_B`
- preserved read:
  - keep the dominant-stage shift explicit instead of extrapolating control intuition into the sweep
- possible downstream consequence:
  - later mixed-axis6 analysis should separate baseline-paired sensitivity from broader mode-sweep sensitivity
