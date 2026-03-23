# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
Extraction mode: `SIM_ULTRA3_FULL_GEOMETRY_STAGE16_AXIS0_ORPHAN_PASS`
Batch scope: residual result-only ultra3 orphan centered on `results_ultra3_full_geometry_stage16_axis0.json`, compared against the earlier ultra strip batches and the catalog-adjacent `results_ultra_big_ax012346.json` without merging them
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra3_full_geometry_stage16_axis0.json`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra3_full_geometry_stage16_axis0.json`
- reason for bounded family:
  - the prior axis0 trajectory-correlation orphan batch explicitly deferred this surface next
  - the current orphan preserves the ultra-strip macro shape:
    - `128` `axis0_ab` entries
    - `48` `stage16` entries
    - `4` stored sequences
    - geometry fields `berry_flux_plus` and `berry_flux_minus`
  - repo-local comparison shows it is closer to the already-batched ultra strip than to `results_ultra_big_ax012346.json`, but it still has no admitted runner source and stays result-only
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`

## 2) Source Membership
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra3_full_geometry_stage16_axis0.json`
  - sha256: `74a1e48f6c9aef13b6613f63d2bfcb469a244397606be4ea7f2a8454506dc88b`
  - size bytes: `25789`
  - line count: `895`
  - source role: geometry-bearing ultra3 result-only orphan with `stage16` and `axis0_ab` branches but no admitted executable source member

## 3) Structural Map Of The Family
### Result structure: `results_ultra3_full_geometry_stage16_axis0.json`
- anchors:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
- source role:
  - one macro result surface with:
    - `axis0_ab`
    - `stage16`
    - `berry_flux_plus`
    - `berry_flux_minus`
    - `seqs`
    - `seeds`
  - bounded counts:
    - `axis0_ab` entry count = `128`
    - `stage16` entry count = `48`
    - `seq` field count = `4`
    - `seed` count = `4`
    - `axis0_trials = 256`
    - `axis0_cycles = 64`
    - `stage_states = 4096`
- strongest bounded reads:
  - `axis0_ab` keeps:
    - `32` absolute `SEQ01` baselines
    - `96` delta records for `SEQ02-04`
  - strongest absolute `axis0_ab` MI case:
    - `T1_FWD_BELL_CNOT_R1_SEQ01`
    - `MI_traj_mean = 0.199553386195354`
    - `neg_SAgB_frac_traj = 0.09749098557692311`
    - `SAgB_traj_mean = 0.45892110357900157`
  - strongest absolute delta `axis0_ab` case:
    - `T1_REV_BELL_CNOT_R1_SEQ04`
    - `dMI = 0.13999170709895817`
    - `dNegFrac = 0.060321514423076955`
    - `dSAgB = -0.13978307120208378`
  - strongest `stage16` case:
    - `T1_outer_1_Se_UP_MIX_A`
    - `dS = 0.0030557656357999537`
    - `dP = -0.002645109343650413`
- bounded implication:
  - the current orphan is a complete ultra macro surface in result form, not a narrow subtable or a topology-only shard

### Geometry layer
- anchors:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
- bounded read:
  - `berry_flux_plus = 6.195918844576741`
  - `berry_flux_minus = -6.195918844576741`
  - sign symmetry is exact at stored precision
  - magnitude remains approximate rather than exact:
    - absolute error vs `2pi` = `0.08726646260284543`
- bounded implication:
  - keep the geometry layer explicit, but do not overstate it as exactly quantized from this source alone

### Stage16 branch
- anchors:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
- bounded read:
  - the `stage16` branch has `48` entries
  - the strongest absolute `dS` and `dP` case is:
    - `T1_outer_1_Se_UP_MIX_A`
  - the dominant Stage16 cell is Se-focused rather than evenly distributed across terrains
- bounded implication:
  - later Stage16 reads should preserve the Se-centered concentration even when the source is wrapped inside an ultra macro surface

### Axis0 AB lattice
- anchors:
  - `results_ultra3_full_geometry_stage16_axis0.json:1-895`
- bounded read:
  - the current orphan uses the same broad record split pattern seen elsewhere in the ultra strip:
    - `SEQ01` absolute records
    - `SEQ02-04` delta records
  - the strongest stored delta again lands on `SEQ04`, but here under:
    - `T1_REV_BELL_CNOT_R1_SEQ04`
  - the absolute baseline MI scale is much larger than the recent axis0 traj-corr v2 orphan and much larger than the local Stage16 effect scale
- bounded implication:
  - do not collapse the file into one uniform metric scale or one uniform record contract

### Separation from the earlier ultra strip
- comparison anchors:
  - `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1/MANIFEST.json`
  - `BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
  - `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
- bounded read:
  - relative to `ultra2`:
    - current orphan expands from `16` to `128` `axis0_ab` entries
    - current orphan keeps `48` `stage16` entries
    - current orphan adds a geometry layer and `4` stored sequences
  - relative to `ultra4`:
    - current orphan keeps geometry, `stage16`, and `axis0_ab`
    - current orphan drops the `axis12` branch
    - current berry-flux magnitude differs from ultra4 by `0.021816615649886906`
  - relative to the final ultra sweep:
    - current orphan keeps the same broad `stage16` plus `axis0_ab` skeleton
    - current orphan retains geometry
    - the sweep drops geometry and adds explicit sweep metadata
- bounded implication:
  - the current orphan sits on the ultra strip seam, but it cannot be merged into any one already-batched ultra family

### Separation from `results_ultra_big_ax012346.json`
- comparison anchors:
  - `results_ultra_big_ax012346.json:1-305`
- bounded read:
  - `ultra_big` stores:
    - `axis0_params`
    - `axis0_traj_metrics`
    - `topology4_metrics`
    - `SEQ01` and `SEQ02` only
    - `num_states = 65536`
    - `lin_trials = 4096`
  - `ultra_big` does not store:
    - `stage16`
    - `berry_flux_plus`
    - `berry_flux_minus`
    - a `128`-entry `axis0_ab` baseline-plus-delta map
- bounded implication:
  - catalog adjacency is not enough to merge `ultra_big` into the current bounded family

### Visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:116,118`
  - negative search for the current filename in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists both:
    - `ultra3_full_geometry_stage16_axis0`
    - `ultra_big_ax012346`
  - the repo-held top-level evidence pack omits both
- bounded implication:
  - the current orphan is catalog-visible by filename alias only and remains unadmitted at the evidence-pack layer

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
  - `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
  - `results_ultra_big_ax012346.json`
  - `SIM_CATALOG_v1.3.md:116,118`
- bounded comparison read:
  - the current orphan is ultra-strip-adjacent by structure
  - it is not identical to the already-batched ultra strip families
  - it is clearly separate from `ultra_big`

## 5) Source-Class Read
- Best classification:
  - residual result-only ultra3 geometry-plus-stage16-plus-axis0 orphan family
- Not best classified as:
  - the same family as `ultra4_full_stack`
  - the same family as `ultra_axis0_ab_axis6_sweep`
  - the same family as `ultra_big_ax012346`
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one macro surface with geometry, `stage16`, and `axis0_ab`
    - `axis0_ab` mixes absolute and delta records
    - `stage16` remains a small Se-focused perturbation layer
  - theory-facing:
    - geometry sign symmetry is exact at stored precision
    - `SEQ04` remains the strongest relative perturbation target inside the `axis0_ab` branch
    - branch scales differ sharply between `stage16` and `axis0_ab`
  - evidence-facing:
    - no runner is admitted as a source member here
    - the catalog lists the file
    - the repo-held evidence pack omits it
- possible downstream consequence:
  - the next residual result-only pass should process `results_ultra_big_ax012346.json` as its own bounded ultra family rather than as an appendage of the current one
