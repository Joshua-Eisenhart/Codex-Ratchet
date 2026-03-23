# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_ultra4_full_stack_family__v1`
Extraction mode: `SIM_ULTRA4_FULL_STACK_PASS`

## T1) The local ultra4 full-stack family exists, but the repo-held top-level evidence pack omits it
- source markers:
  - `run_ultra4_full_stack.py:1-412`
  - negative search for `S_SIM_ULTRA4_FULL_STACK` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_CATALOG_v1.3.md:131`
- tension:
  - the current runner writes local evidence for `S_SIM_ULTRA4_FULL_STACK`
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block
- preserved read:
  - keep local-writer existence distinct from repo-top evidence admission
- possible downstream consequence:
  - this batch should stay proposal-side in provenance strength

## T2) The `axis0_ab` branch mixes absolute and delta record types inside one map
- source markers:
  - `run_ultra4_full_stack.py:332-412`
  - `results_ultra4_full_stack.json`
- tension:
  - `SEQ01` records store absolute:
    - `MI_traj_mean`
    - `SAgB_traj_mean`
    - `neg_SAgB_frac_traj`
  - `SEQ02` through `SEQ04` records store only:
    - `dMI`
    - `dSAgB`
    - `dNegFrac`
- preserved read:
  - do not speak about one uniform `axis0_ab` record contract
- possible downstream consequence:
  - later Axis0 reads must distinguish baseline records from relative records

## T3) Berry-flux sign symmetry is exact at stored precision, but the magnitude is only approximate
- source markers:
  - `run_ultra4_full_stack.py:39-58`
  - `results_ultra4_full_stack.json`
- tension:
  - `berry_flux_plus = 6.217735460226628`
  - `berry_flux_minus = -6.217735460226628`
  - the code comment frames the target as `±2π`, but the stored magnitude is below that expectation
- preserved read:
  - keep both the sign symmetry and the non-exact magnitude
- possible downstream consequence:
  - later geometry summaries should avoid overstating the Berry-flux layer as exactly quantized from this source alone

## T4) Stage16 and Axis0 AB branches live on very different effect scales inside the same full-stack file
- source markers:
  - `results_ultra4_full_stack.json`
- tension:
  - the strongest Stage16 absolute effect is about `0.00304873827915781`
  - the strongest Axis0 AB delta reaches about `0.1396523788319004`
- preserved read:
  - do not speak about one uniform ultra4 effect scale
- possible downstream consequence:
  - later interpretation should stay branch-specific rather than stack-averaged

## T5) The strongest Stage16 cells remain Se-focused even in the full-stack expansion
- source markers:
  - `results_ultra4_full_stack.json`
- tension:
  - the top Stage16 entries are:
    - `T1_outer_1_Se_UP_MIX_A`
    - `T1_inner_1_Se_DOWN_MIX_B`
    - `T2_inner_1_Se_DOWN_MIX_B`
    - `T2_outer_1_Se_UP_MIX_A`
- preserved read:
  - keep the Stage16 branch Se-centered rather than implying a broad even distribution
- possible downstream consequence:
  - later Stage16 summaries should preserve the Se concentration even inside the larger full-stack shell

## T6) Raw-order-adjacent `ultra_axis0_ab_axis6_sweep` is a narrower sweep family, not the same bounded full stack
- source markers:
  - `run_ultra_axis0_ab_axis6_sweep.py:300-398`
  - `results_ultra_axis0_ab_axis6_sweep.json:1-912`
- tension:
  - `ultra_axis0_ab_axis6_sweep` keeps `stage16` and `axis0_ab`
  - it drops `berry_flux_plus`, `berry_flux_minus`, and `axis12`
  - it adds explicit sweep metadata:
    - `entanglers`
    - `entangle_reps_list`
    - `mix_modes`
- preserved read:
  - the ultra sweep begins the next bounded family
- possible downstream consequence:
  - the next batch should start at `run_ultra_axis0_ab_axis6_sweep.py`
