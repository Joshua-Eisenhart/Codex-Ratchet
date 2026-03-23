# A2-2 REFINED CANDIDATES

## Candidate 1: AXIS0_BOOKKEEP_ORPHAN_SLICE_SHELL

- status: `A2_2_CANDIDATE`
- type: `result-only orphan shell`
- claim:
  - `results_axis0_boundary_bookkeep_v1.json` is a bounded one-file result-only orphan slice and should remain a standalone packet rather than being reabsorbed into larger neighboring families
- source lineage:
  - parent batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
  - parent basis: cluster A, distillate D1, candidates C1-C3
- retained boundary:
  - source membership remains one file only

## Candidate 2: EXACT_SWEEP_SLICE_ANCHOR

- status: `A2_2_CANDIDATE`
- type: `family anchor packet`
- claim:
  - the orphan has an exact overlapping-metric anchor to the already-batched boundary/bookkeep sweep family at the `sign1` `REC1` BELL and GINIBRE slice, so orphan status here does not mean source-unanchored status
- source lineage:
  - parent basis: cluster C, tension T1, distillate D2, candidate C4
- retained contradiction marker:
  - standalone source membership survives
  - exact sweep-family anchoring survives

## Candidate 3: ENRICHED_SLICE_NOT_REDUNDANT_DUPLICATE

- status: `A2_2_CANDIDATE`
- type: `nonredundant derivative packet`
- claim:
  - the current orphan duplicates the sweep slice on shared means but adds extrema and zero-negativity fields, so it is a compact enriched derivative rather than a redundant duplicate
- source lineage:
  - parent basis: cluster C, tension T2, distillate D3
- retained contradiction marker:
  - shared means remain exact
  - local enrichment remains additional

## Candidate 4: BELL_GINIBRE_BOOKKEEPING_WITH_ZERO_NEGATIVITY

- status: `A2_2_CANDIDATE`
- type: `payload contrast packet`
- claim:
  - the orphan carries a strong BELL-vs-GINIBRE bookkeeping displacement, with BELL much larger on `dMI_mean`, while all stored negativity fractions remain zero, so displacement must not be retold as negativity production
- source lineage:
  - parent basis: cluster B, tension T3, distillate D4, candidate C3
- retained contradiction marker:
  - strong init-class separation survives
  - stored negativity remains zero

## Candidate 5: CATALOG_VISIBLE_EVIDENCE_OMITTED_SLICE

- status: `A2_2_CANDIDATE`
- type: `visibility seam packet`
- claim:
  - the orphan is catalog-visible by filename alias only while the top-level evidence pack omits it entirely, so catalog presence remains weaker than evidence admission
- source lineage:
  - parent basis: cluster E, tension T5, distillate D5
- retained contradiction marker:
  - filename visibility survives
  - evidence-pack visibility does not

## Candidate 6: TRAJ_CORR_V2_NONMERGE_BOUNDARY

- status: `A2_2_CANDIDATE`
- type: `adjacent-family separation packet`
- claim:
  - `results_axis0_traj_corr_suite_v2.json` stays outside this batch because its 128-case trajectory lattice and metric contract are fundamentally different, even though it is catalog-adjacent and also evidence-omitted
- source lineage:
  - parent basis: cluster D, tension T4, distillates D1 and D6, candidate C5
- retained boundary:
  - do not merge the trajectory orphan into this bookkeeping slice on adjacency alone
