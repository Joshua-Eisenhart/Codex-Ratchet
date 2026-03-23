# CONTRADICTION PRESERVATION

## Preserved Contradictions

1. Orphan status vs exact family anchor
- preserved:
  - the current surface stands alone in source membership
  - it has exact overlapping mean metrics with an already-batched sweep family slice
- not collapsed into:
  - "orphan means unanchored" or "exact anchoring means this is no longer a standalone orphan packet"

2. Derivative relation vs nonredundancy
- preserved:
  - the current surface is derivative of the sweep family
  - it stores additional extrema and zero-negativity fields absent from the matching sweep slice
- not collapsed into:
  - "this is just a duplicate extract"

3. Large displacement vs zero negativity
- preserved:
  - BELL carries much larger bookkeeping displacement than GINIBRE
  - all stored negativity fractions remain zero
- not collapsed into:
  - "large bookkeeping movement implies negativity production"

4. Catalog adjacency vs family membership
- preserved:
  - the current orphan and `traj_corr_suite_v2` are both catalog-visible and evidence-omitted
  - their lattices and metric contracts differ materially
- not collapsed into:
  - "adjacent catalog entries belong in one bounded family"

5. Better anchor quality vs no direct runner hit
- preserved:
  - the current orphan has no direct runner-name hit in `simpy/`
  - it still has stronger anchor quality than the deferred trajectory orphan because the sweep overlap is exact
- not collapsed into:
  - "lack of runner hit makes both orphans equally unanchored"

## Quarantine Rules

- quarantine reason: `the orphan is not treated as disconnected from the sweep family`
- quarantine reason: `the orphan is not treated as a redundant duplicate of the sweep slice`
- quarantine reason: `bookkeeping displacement is not treated as negativity`
- quarantine reason: `catalog presence is not treated as evidence-pack admission`
- quarantine reason: `traj_corr_suite_v2 is not admitted into this slice by adjacency`
