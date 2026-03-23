# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
Extraction mode: `SIM_ULTRA3_FULL_GEOMETRY_STAGE16_AXIS0_ORPHAN_PASS`

## T1) The local ultra3 geometry-stage16-axis0 surface exists in the catalog, but the repo-held top-level evidence pack omits it
- source markers:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
  - `SIM_CATALOG_v1.3.md:116`
  - negative search for `ultra3_full_geometry_stage16_axis0` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the file is catalog-visible
  - the repo-held evidence pack contains no matching block
  - no runner is admitted as a source member in the current bounded batch
- preserved read:
  - keep catalog presence distinct from evidence admission and from executable provenance
- possible downstream consequence:
  - this batch should stay proposal-side in provenance strength

## T2) The `axis0_ab` branch mixes absolute and delta record types inside one map
- source markers:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
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
  - later ultra-axis reads must distinguish baseline records from relative records

## T3) Berry-flux sign symmetry is exact at stored precision, but the magnitude is only approximate and differs from ultra4
- source markers:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
  - `BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
- tension:
  - current values are:
    - `berry_flux_plus = 6.195918844576741`
    - `berry_flux_minus = -6.195918844576741`
  - the magnitude is not exact `±2pi`
  - the current magnitude differs from ultra4 by `0.021816615649886906`
- preserved read:
  - keep both the exact sign symmetry and the non-identical magnitude
- possible downstream consequence:
  - later geometry summaries should avoid collapsing ultra3 and ultra4 into one identical geometry layer

## T4) Stage16 and Axis0 AB branches live on very different effect scales inside the same orphan file
- source markers:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
- tension:
  - strongest absolute Stage16 `|dS|` is `0.0030557656357999537`
  - strongest absolute Axis0 AB `|dMI|` delta is `0.13999170709895817`
- preserved read:
  - do not speak about one uniform ultra3 effect scale
- possible downstream consequence:
  - later interpretation should stay branch-specific rather than stack-averaged

## T5) Ultra3 belongs near the earlier ultra strip, but it cannot be merged into any one already-batched ultra family
- source markers:
  - `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1/MANIFEST.json`
  - `BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
  - `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
- tension:
  - current orphan shares `stage16` and `axis0_ab` with the ultra strip
  - current orphan keeps geometry like ultra4
  - current orphan drops `axis12` unlike ultra4
  - current orphan keeps geometry unlike the final ultra sweep
- preserved read:
  - ultra3 is a seam family, not a duplicate of ultra2, ultra4, or the ultra sweep
- possible downstream consequence:
  - later ultra synthesis should preserve ultra3 as a separate middle seam

## T6) Catalog-adjacent `ultra_big_ax012346` is not the same bounded family
- source markers:
  - `results_ultra_big_ax012346.json:1-305`
  - `SIM_CATALOG_v1.3.md:118`
- tension:
  - `ultra_big` stores:
    - `axis0_traj_metrics`
    - `topology4_metrics`
    - `SEQ01` and `SEQ02` only
  - `ultra_big` omits:
    - `stage16`
    - berry flux
    - the `128`-entry `axis0_ab` lattice
- preserved read:
  - `ultra_big` begins the next bounded family
- possible downstream consequence:
  - the next residual result-only pass should process `results_ultra_big_ax012346.json` separately
