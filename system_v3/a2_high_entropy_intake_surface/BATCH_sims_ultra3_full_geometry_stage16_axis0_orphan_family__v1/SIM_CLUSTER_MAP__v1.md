# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
Extraction mode: `SIM_ULTRA3_FULL_GEOMETRY_STAGE16_AXIS0_ORPHAN_PASS`

## Cluster A
- cluster label:
  - core orphan family
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra3_full_geometry_stage16_axis0.json`
- family role:
  - canonical source-bounded member set for this batch
- executable-facing read:
  - one result-only ultra macro surface
  - no runner admitted as a source member
- tension anchor:
  - the family is structurally rich and ultra-strip-adjacent, but source membership remains one orphan result surface

## Cluster B
- cluster label:
  - geometry layer
- members:
  - `berry_flux_plus`
  - `berry_flux_minus`
  - `n_vec`
  - `theta`
- family role:
  - geometric shell around the ultra orphan
- executable-facing read:
  - sign symmetry is exact at stored precision
  - the magnitude remains approximate rather than exact
- tension anchor:
  - geometry presence makes the current orphan closer to ultra4 than to the final ultra sweep, but not identical to ultra4

## Cluster C
- cluster label:
  - stage16 layer
- members:
  - `48` `stage16` entries
  - `T1_outer_1_Se_UP_MIX_A`
  - `T1_inner_1_Se_DOWN_MIX_B`
  - `dS`
  - `dP`
- family role:
  - small-effect Stage16 perturbation surface
- executable-facing read:
  - the strongest stored Stage16 cell is Se-focused
  - Stage16 effects remain much smaller than the strongest `axis0_ab` deltas
- tension anchor:
  - the file is one macro family, but its Stage16 branch lives on a different effect scale from the Axis0 branch

## Cluster D
- cluster label:
  - axis0_ab lattice
- members:
  - `128` `axis0_ab` entries
  - `32` absolute `SEQ01` baselines
  - `96` delta entries for `SEQ02-04`
  - `T1`
  - `T2`
  - `FWD`
  - `REV`
  - `BELL`
  - `GINIBRE`
  - `CNOT`
  - `CZ`
  - `R1`
  - `R2`
- family role:
  - main trajectory-correlation lattice inside the orphan
- executable-facing read:
  - strongest absolute baseline MI is `T1_FWD_BELL_CNOT_R1_SEQ01`
  - strongest delta response is `T1_REV_BELL_CNOT_R1_SEQ04`
- tension anchor:
  - the branch mixes absolute and delta record types inside one map

## Cluster E
- cluster label:
  - ultra-strip comparison seam
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra4_full_stack_family__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
- family role:
  - comparison-only ultra continuity seam
- executable-facing read:
  - the current orphan belongs near the ultra strip by structure
  - it drops `axis12` relative to ultra4 and keeps geometry relative to the final sweep
- tension anchor:
  - structural continuity exists without identity of family membership

## Cluster F
- cluster label:
  - deferred ultra_big separation anchor
- members:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra_big_ax012346.json`
- family role:
  - next bounded-family boundary anchor
- executable-facing read:
  - `ultra_big` is a different macro surface:
    - `axis0_traj_metrics`
    - `topology4_metrics`
    - `SEQ01` and `SEQ02` only
- tension anchor:
  - catalog adjacency could tempt an incorrect merge even though the contracts differ materially

## Cross-Cluster Read
- Cluster A is the only in-batch source family
- Cluster B, Cluster C, and Cluster D show the geometry-plus-stage16-plus-axis0 composition of the orphan
- Cluster E preserves continuity with the earlier ultra strip without collapsing the seam
- Cluster F preserves the next bounded-family split against `ultra_big`
