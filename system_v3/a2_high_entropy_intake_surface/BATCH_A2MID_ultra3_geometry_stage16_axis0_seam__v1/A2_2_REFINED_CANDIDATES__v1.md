# A2-2 REFINED CANDIDATES

## Candidate 1: ULTRA3_GEOMETRY_STAGE16_AXIS0_SHELL

- status: `A2_2_CANDIDATE`
- type: `result-only ultra seam shell`
- claim:
  - `results_ultra3_full_geometry_stage16_axis0.json` is a bounded one-file ultra orphan surface and should remain its own seam packet rather than being reabsorbed into nearby ultra families
- source lineage:
  - parent batch: `BATCH_sims_ultra3_full_geometry_stage16_axis0_orphan_family__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - source membership remains one file only

## Candidate 2: BERRY_FLUX_SIGN_SYMMETRY_WITH_APPROX_MAGNITUDE

- status: `A2_2_CANDIDATE`
- type: `geometry packet`
- claim:
  - the ultra3 geometry layer keeps exact sign symmetry at stored precision, but its berry-flux magnitude is only approximate and differs from ultra4, so geometry continuity does not justify family identity
- source lineage:
  - parent basis: cluster B, tension T3, distillates D2 and D6, candidate C4
- retained contradiction marker:
  - exact sign symmetry survives
  - exact `±2pi` and ultra4 identity do not

## Candidate 3: STAGE16_AXIS0AB_BRANCH_SCALE_SPLIT

- status: `A2_2_CANDIDATE`
- type: `branch-scale packet`
- claim:
  - the file is one macro surface, but its `stage16` and `axis0_ab` branches live on very different effect scales: `stage16` is small and Se-centered while the strongest `axis0_ab` delta is much larger
- source lineage:
  - parent basis: clusters C and D, tension T4, distillate D3
- retained contradiction marker:
  - one macro shell survives
  - one uniform effect scale does not

## Candidate 4: AXIS0AB_MIXED_BASELINE_DELTA_CONTRACT

- status: `A2_2_CANDIDATE`
- type: `axis0_ab contract packet`
- claim:
  - the `axis0_ab` branch does not have one uniform record contract: `SEQ01` entries store absolutes while `SEQ02-04` store deltas, so branch summaries must preserve baseline-vs-relative record type separation
- source lineage:
  - parent basis: cluster D, tension T2, distillate D2
- retained boundary:
  - do not flatten the `axis0_ab` map into one record type

## Candidate 5: ULTRA3_MIDDLE_SEAM_NOT_ULTRA4_OR_SWEEP

- status: `A2_2_CANDIDATE`
- type: `ultra-strip seam packet`
- claim:
  - ultra3 belongs near the earlier ultra strip but remains a middle seam: it keeps geometry like ultra4 while dropping axis12, and it keeps `stage16` plus `axis0_ab` like the final ultra sweep while retaining geometry that the final sweep lacks
- source lineage:
  - parent basis: cluster E, tension T5, distillate D4, candidate C4
- retained contradiction marker:
  - structural continuity survives
  - identity with any one earlier ultra family does not

## Candidate 6: ULTRABIG_NONMERGE_WITH_CATALOG_ONLY_VISIBILITY

- status: `A2_2_CANDIDATE`
- type: `next-family and visibility fence`
- claim:
  - `ultra_big_ax012346` remains the next bounded family because it lacks berry flux, `stage16`, and the `128`-entry `axis0_ab` lattice; both surfaces may be catalog-visible, but neither adjacency nor filename visibility upgrades the current ultra3 orphan into evidence-admitted status
- source lineage:
  - parent basis: cluster F, tensions T1 and T6, distillates D5 and D6, candidate C5
- retained contradiction marker:
  - catalog visibility survives
  - `ultra_big` equivalence and evidence admission do not
