# SELECTION RATIONALE

- selected parent batch: `BATCH_sims_axis0_boundary_bookkeep_v1_orphan_slice__v1`
- selection reason: it is the strongest remaining result-only orphan with an exact family anchor, local enrichment beyond that anchor, and an explicitly preserved non-merge boundary against an adjacent but structurally different orphan

## Why This Batch Now

- the harden result-only branch is closed, so the next clean residual move is the anchored axis0 bookkeeping orphan
- the parent batch already isolates the strongest reusable seams:
  - exact overlap with the sweep family
  - nonredundant local enrichment
  - strong BELL-vs-GINIBRE displacement at zero negativity
  - catalog adjacency without trajectory-family merge
- the next orphan `results_axis0_traj_corr_suite_v2.json` is already defined as separate, so this pass can stay narrow

## What Was Kept

- the one-file result-only orphan shell
- exact sweep-family slice linkage
- extra extrema and zero-negativity fields beyond the sweep slice
- strong BELL-vs-GINIBRE bookkeeping contrast
- catalog-only visibility with no evidence-pack admission
- non-merge boundary against `traj_corr_suite_v2`

## What Was Reduced Away

- repeated parent prose about catalog line windows
- repeated listing of all extra fields in multiple places
- omnibus framing that would merge:
  - the current orphan slice
  - the already-batched sweep family
  - the adjacent trajectory orphan

## Why Candidate, Not Promotion

- orphan status and exact family anchoring still coexist as a tension rather than a settled promotion rule
- the current surface is derivative of the sweep family but not redundant
- catalog visibility remains weaker than evidence-pack admission
