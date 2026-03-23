# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1`
Extraction mode: `SIM_ULTRA_AXIS0_AB_AXIS6_SWEEP_PASS`

## T1) The local ultra sweep family exists, but the repo-held top-level evidence pack omits it
- source markers:
  - `run_ultra_axis0_ab_axis6_sweep.py:1-398`
  - negative search for `S_SIM_ULTRA_AXIS0_AB_STAGE16_AXIS6_SWEEP` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_CATALOG_v1.3.md:117`
- tension:
  - the current runner writes local evidence for `S_SIM_ULTRA_AXIS0_AB_STAGE16_AXIS6_SWEEP`
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block
- preserved read:
  - keep local-writer existence distinct from repo-top evidence admission
- possible downstream consequence:
  - this final raw-order batch still stays proposal-side in provenance strength

## T2) The `axis0_ab` branch mixes absolute and delta record types inside one map
- source markers:
  - `run_ultra_axis0_ab_axis6_sweep.py:332-398`
  - `results_ultra_axis0_ab_axis6_sweep.json`
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

## T3) The current sweep keeps the `ultra4` keysets but not the `ultra4` value regime
- source markers:
  - `results_ultra4_full_stack.json`
  - `results_ultra_axis0_ab_axis6_sweep.json`
- tension:
  - the Stage16 keyset is the same as `ultra4`
  - the Axis0 AB keyset is the same as `ultra4`
  - values differ materially:
    - `T1_inner_1_Se_DOWN_MIX_B` in `ultra4` has `dS = -0.003048738279157809`
    - the current sweep has `dS = -0.00636023707760236`
- preserved read:
  - do not collapse the current sweep into “ultra4 without geometry”
- possible downstream consequence:
  - later summaries should preserve that the narrowing changed results, not just exposed a subset

## T4) Stage16 and Axis0 AB branches still live on different effect scales
- source markers:
  - `results_ultra_axis0_ab_axis6_sweep.json`
- tension:
  - the strongest Stage16 absolute effect is about `0.00636023707760236`
  - the strongest Axis0 AB delta reaches about `0.13975440288608165`
- preserved read:
  - do not speak about one uniform sweep effect scale
- possible downstream consequence:
  - later interpretation should stay branch-specific rather than bundle-averaged

## T5) The strongest Stage16 cells stay Se-focused even in the final sweep family
- source markers:
  - `results_ultra_axis0_ab_axis6_sweep.json`
- tension:
  - the top Stage16 entries are:
    - `T1_inner_1_Se_DOWN_MIX_B`
    - `T2_inner_1_Se_DOWN_MIX_B`
    - `T1_outer_1_Se_UP_MIX_B`
    - `T1_inner_1_Se_DOWN_MIX_A`
- preserved read:
  - keep the Stage16 branch Se-centered rather than implying a broad even distribution
- possible downstream consequence:
  - later Stage16 summaries should preserve the Se concentration even at the end of the ultra strip

## T6) The raw `simpy/` strip ends here
- source markers:
  - filename inventory of `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy`
- tension:
  - this file is index `51 / 51`
  - no later raw-order `simpy/` file remains after `run_ultra_axis0_ab_axis6_sweep.py`
- preserved read:
  - the current batch closes the bounded raw-order `simpy/` family extraction campaign
- possible downstream consequence:
  - any further work should switch from raw-order family extraction to closure audit, residual inventory, or synthesis over already-batched sims sources
