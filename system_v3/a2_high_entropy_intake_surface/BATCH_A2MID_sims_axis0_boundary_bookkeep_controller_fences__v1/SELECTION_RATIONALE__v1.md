# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID BATCH SELECTION NOTE
Batch: `BATCH_A2MID_sims_axis0_boundary_bookkeep_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## 1) Selected Parent Batch
Selected parent:
- `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`

## 2) Why This Was The Next A2-Mid Target
Selection basis:
- it was the first immediate reduction target on the controller action board
- it is a bounded sims orphan with clear source anchor quality and clear anti-merge value
- it yields a smaller controller packet for provenance, enrichment, negativity discipline, and residual sequencing without reopening raw sims files

Why it is worth a bounded A2-mid pass now:
- the parent already isolates the exact sweep-family overlap that keeps the orphan source-anchored
- the parent already separates enrichment from redundancy
- the parent already blocks merger with the adjacent `traj_corr_suite_v2` orphan
- the parent already preserves the catalog-versus-evidence distinction the controller needs for queue decisions

## 3) Deferred Alternatives
Deferred next existing intake batch:
- `BATCH_sims_axis0_traj_corr_suite_v2_orphan_family__v1`
- `BATCH_refinedfuel_nonsims_game_theory_rosetta_personality_analogy__v1`

Reason for deferral:
- the current boundary/bookkeep orphan was already first in the immediate tranche
- reducing it first preserves the cleaner family-anchor and anti-merge rule before moving into the more complex `traj_corr_suite_v2` lattice
- the refined-fuel overlay-governance follow-on remains strong, but the active queue still had one higher-priority sims orphan in front of it

## 4) Narrowing Choice Inside The Selected Parent
This reduction batch deliberately keeps only:
- sweep-anchor preservation for a bounded orphan slice
- nonredundant enriched-slice handling
- BELL-vs-GINIBRE bookkeeping displacement with zero stored negativity
- separate-family handling for `traj_corr_suite_v2`
- catalog-versus-evidence noncollapse

This reduction batch deliberately quarantines:
- orphan status retold as lack of family anchor
- overlap retold as pure redundancy
- catalog adjacency retold as merge permission
- bookkeeping magnitude retold as negativity proof
- catalog presence retold as evidence admission

## 5) Batch Result Type
Result type for this pass:
- sims provenance and anti-merge reduction
- contradiction-preserving
- source-linked to the parent intake batch
- proposal-side only

This is not:
- a raw sims reread
- a runner reconstruction pass
- a merge of the boundary/bookkeep orphan with trajectory-correlation surfaces
- an A2-1 promotion
